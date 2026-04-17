from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from apps.users.models import LoginAttempt

from .models import BlockedIP, FailedLoginAttempt, KnownDevice
from .utils import get_client_ip, log_security_event


MAX_ATTEMPTS = 5
LOCK_TIME = 10
WINDOW_MINUTES = 10


def register_failed_attempt(email, ip):
    record, _ = FailedLoginAttempt.objects.get_or_create(
        email=email,
        ip_address=ip,
    )

    if record.locked_until and record.locked_until <= timezone.now():
        record.attempts = 0
        record.locked_until = None

    record.attempts += 1
    record.last_attempt = timezone.now()

    if record.attempts >= MAX_ATTEMPTS:
        record.locked_until = timezone.now() + timedelta(minutes=LOCK_TIME)

    record.save()
    return record


def reset_attempts(email, ip):
    FailedLoginAttempt.objects.filter(email=email, ip_address=ip).delete()


def is_account_locked(email, ip):
    record = FailedLoginAttempt.objects.filter(
        email=email,
        ip_address=ip,
    ).first()
    return record.is_locked() if record else False


class SecurityAnalyticsService:
    @staticmethod
    def record_login_attempt(email, ip_address, user_agent, success):
        LoginAttempt.objects.create(
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
        )

        if success:
            return

        window = timezone.now() - timedelta(minutes=WINDOW_MINUTES)
        attempts = LoginAttempt.objects.filter(
            ip_address=ip_address,
            success=False,
            created_at__gte=window,
        ).count()

        if attempts >= MAX_ATTEMPTS:
            BlockedIP.objects.update_or_create(
                ip_address=ip_address,
                defaults={
                    "reason": "Too many failed login attempts",
                    "blocked_until": timezone.now() + timedelta(minutes=LOCK_TIME),
                    "attempts": attempts,
                },
            )


class AttackDetectionService:
    MAX_FAILED_ATTEMPTS = 20
    WINDOW_MINUTES = 10

    @staticmethod
    def check_and_block_ip(ip):
        window_start = timezone.now() - timedelta(
            minutes=AttackDetectionService.WINDOW_MINUTES
        )
        attempts = LoginAttempt.objects.filter(
            ip_address=ip,
            success=False,
            created_at__gte=window_start,
        ).count()

        if attempts >= AttackDetectionService.MAX_FAILED_ATTEMPTS:
            BlockedIP.objects.update_or_create(
                ip_address=ip,
                defaults={
                    "reason": "Too many failed login attempts",
                    "blocked_until": timezone.now() + timedelta(minutes=30),
                    "attempts": attempts,
                },
            )


class DeviceDetectionService:
    @staticmethod
    def detect_new_device(user, request):
        device = request.META.get("HTTP_USER_AGENT", "Unknown device")
        ip = get_client_ip(request) or "127.0.0.1"

        known_device, created = KnownDevice.objects.get_or_create(
            user=user,
            device=device,
            defaults={"ip_address": ip},
        )

        if created:
            log_security_event(
                user=user,
                event_type="LOGIN_SUCCESS",
                request=request,
                metadata={"device": device, "new_device": True},
            )
            SecurityEmailService.send_new_device_alert(user=user, device=device, ip=ip)
            return

        if known_device.ip_address != ip:
            known_device.ip_address = ip
            known_device.save(update_fields=["ip_address", "last_seen"])


class SecurityEmailService:
    @staticmethod
    def send_new_device_alert(user, device, ip):
        subject = "New Device Login Detected"
        message = (
            f"Hello {user.email},\n\n"
            "We detected a login from a new device.\n\n"
            f"Device: {device}\n"
            f"IP Address: {ip}\n\n"
            "If this was not you, please reset your password immediately.\n"
        )

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )

    @staticmethod
    def send_password_changed_alert(user):
        subject = "Your Password Was Changed"
        message = (
            f"Hello {user.email},\n\n"
            "Your account password has been successfully changed.\n\n"
            "If you did not perform this action, please contact support immediately.\n"
        )

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )


BLOCK_DURATION = timedelta(minutes=30)


def handle_failed_login(ip):
    blocked_ip, created = BlockedIP.objects.get_or_create(
        ip_address=ip,
        defaults={
            "attempts": 1,
            "reason": "Too many failed login attempts",
            "blocked_until": timezone.now() + BLOCK_DURATION,
            "block_count": 1,
        },
    )

    if created:
        return blocked_ip

    blocked_ip.attempts += 1
    if blocked_ip.attempts >= MAX_ATTEMPTS:
        blocked_ip.reason = "Too many failed login attempts"
        blocked_ip.blocked_until = timezone.now() + BLOCK_DURATION
        blocked_ip.block_count += 1
    blocked_ip.save()
    return blocked_ip
