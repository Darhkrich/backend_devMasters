from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.security.models import BlockedIP, SecurityAlert, UserSession
from apps.users.models import DeviceSession, FailedLoginAttempt, LoginAttempt, LoginHistory, SecurityEvent


class Command(BaseCommand):
    help = "Purge or report expired data according to configured retention policies."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        now = timezone.now()
        dry_run = options["dry_run"]

        operations = [
            (
                "audit_logs",
                AuditLog.objects.filter(retention_until__lt=now),
            ),
            (
                "security_events",
                SecurityEvent.objects.filter(
                    created_at__lt=now - timedelta(days=settings.SECURITY_EVENT_RETENTION_DAYS)
                ),
            ),
            (
                "login_history",
                LoginHistory.objects.filter(
                    created_at__lt=now - timedelta(days=settings.LOGIN_HISTORY_RETENTION_DAYS)
                ),
            ),
            (
                "login_attempts",
                LoginAttempt.objects.filter(
                    created_at__lt=now - timedelta(days=settings.SECURITY_EVENT_RETENTION_DAYS)
                ),
            ),
            (
                "failed_login_attempts",
                FailedLoginAttempt.objects.filter(
                    created_at__lt=now - timedelta(days=settings.SECURITY_EVENT_RETENTION_DAYS)
                ),
            ),
            (
                "security_alerts",
                SecurityAlert.objects.filter(
                    created_at__lt=now - timedelta(days=settings.SECURITY_EVENT_RETENTION_DAYS),
                    resolved=True,
                ),
            ),
            (
                "expired_blocks",
                BlockedIP.objects.filter(blocked_until__lt=now),
            ),
            (
                "device_sessions",
                DeviceSession.objects.filter(
                    created_at__lt=now - timedelta(days=settings.DEVICE_SESSION_RETENTION_DAYS)
                ).filter(is_active=False),
            ),
            (
                "user_sessions",
                UserSession.objects.filter(
                    created_at__lt=now - timedelta(days=settings.DEVICE_SESSION_RETENTION_DAYS),
                    is_active=False,
                ),
            ),
        ]

        for label, queryset in operations:
            count = queryset.count()
            if not dry_run and count:
                queryset.delete()
            self.stdout.write(f"{label}: {count} {'would be deleted' if dry_run else 'deleted'}")
