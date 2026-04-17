from datetime import timedelta

from django.utils import timezone

from apps.users.models import SecurityEvent

from .models import KnownDevice, SecurityAlert, UserSession

import hashlib

def log_security_event(user, event_type, request=None, metadata=None):
    ip = None
    user_agent = None

    if request:
        ip = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")

    SecurityEvent.objects.create(
        user=user,
        event_type=event_type,
        ip_address=ip,
        user_agent=user_agent,
        metadata=metadata,
    )


def create_alert(user, message, severity="low", ip=None, title=None):
    SecurityAlert.objects.create(
        user=user,
        title=title or "Security alert",
        message=message,
        severity=severity,
        ip_address=ip,
    )


def alert_on_repeated_security_events(
    event_type,
    *,
    user=None,
    ip=None,
    threshold=3,
    window_minutes=15,
    title="Security anomaly detected",
    message="Repeated high-risk activity was detected.",
    severity="medium",
):
    since = timezone.now() - timedelta(minutes=window_minutes)
    queryset = SecurityEvent.objects.filter(
        event_type=event_type,
        created_at__gte=since,
    )

    if user:
        queryset = queryset.filter(user=user)
    elif ip:
        queryset = queryset.filter(ip_address=ip)

    if queryset.count() >= threshold:
        create_alert(user, message, severity=severity, ip=ip, title=title)


def detect_suspicious_login(user, ip, device):
    now = timezone.now()

    recent_sessions = UserSession.objects.filter(
        user=user,
        created_at__gte=now - timedelta(minutes=5),
    ).count()
    if recent_sessions > 3:
        create_alert(
            user,
            "Multiple logins detected within five minutes.",
            severity="high",
            ip=ip,
            title="Multiple recent logins",
        )

    known_device, created = KnownDevice.objects.get_or_create(
        user=user,
        device=device,
        defaults={"ip_address": ip or "127.0.0.1"},
    )
    if created:
        create_alert(
            user,
            f"New device detected: {device}",
            severity="medium",
            ip=ip,
            title="New device login",
        )
    elif ip and known_device.ip_address != ip:
        known_device.ip_address = ip
        known_device.save(update_fields=["ip_address", "last_seen"])
        create_alert(
            user,
            "Login from a new IP address for a known device.",
            severity="medium",
            ip=ip,
            title="New IP detected",
        )


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")




def generate_device_fingerprint(request):
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    accept_lang = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
    ip = get_client_ip(request)  # use your existing function

    raw = f"{user_agent}:{accept_lang}:{ip}"
    return hashlib.sha256(raw.encode()).hexdigest()
