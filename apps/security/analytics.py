from datetime import timedelta

from django.conf import settings
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.core.cache import cache_get_or_set
from apps.security.models import BlockedIP
from apps.users.models import DeviceSession, LoginAttempt, LoginHistory, SecurityEvent, User


def admin_security_dashboard():
    def builder():
        last_24h = timezone.now() - timedelta(hours=24)
        recent_security_events = SecurityEvent.objects.select_related("user")[:20]
        return {
            "total_users": User.objects.count(),
            "failed_logins_24h": LoginAttempt.objects.filter(
                success=False,
                created_at__gte=last_24h,
            ).count(),
            "successful_logins_24h": LoginAttempt.objects.filter(
                success=True,
                created_at__gte=last_24h,
            ).count(),
            "locked_accounts": User.objects.filter(
                account_locked_until__gt=timezone.now()
            ).count(),
            "blocked_ips": BlockedIP.objects.count(),
            "recent_security_events": [
                {
                    "event": event.event_type,
                    "user": event.user.email if event.user else None,
                    "time": event.created_at,
                }
                for event in recent_security_events
            ],
        }

    return cache_get_or_set(
        "security.dashboard",
        timeout=settings.API_CACHE_TTL_SECONDS,
        builder=builder,
    )


def login_trend():
    def builder():
        data = (
            LoginHistory.objects.annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )
        return [{"date": row["date"].strftime("%a"), "count": row["count"]} for row in data]

    return cache_get_or_set(
        "security.login_trend",
        timeout=settings.API_CACHE_TTL_SECONDS,
        builder=builder,
    )


def admin_dashboard_stats():
    def builder():
        return {
            "total_users": User.objects.count(),
            "active_users": User.objects.filter(is_active=True).count(),
            "suspended_users": User.objects.filter(is_active=False).count(),
            "admins": User.objects.filter(is_staff=True).count(),
            "logins_today": LoginHistory.objects.filter(
                created_at__date=timezone.now().date()
            ).count(),
            "security_alerts": SecurityEvent.objects.count(),
        }

    return cache_get_or_set(
        "security.admin_stats",
        timeout=settings.API_CACHE_TTL_SECONDS,
        builder=builder,
    )


def admin_dashboard_overview():
    def builder():
        last_7_days = []
        for offset in range(6, -1, -1):
            day = timezone.now().date() - timedelta(days=offset)
            last_7_days.append(
                {
                    "date": day.strftime("%a"),
                    "users": User.objects.filter(date_joined__date=day).count(),
                }
            )
        return {
            "stats": {
                "total_users": User.objects.count(),
                "active_sessions": DeviceSession.objects.filter(is_active=True).count(),
                "blocked_ips": BlockedIP.objects.count(),
                "suspicious_logins": SecurityEvent.objects.filter(
                    event_type="LOGIN_FAILED"
                ).count(),
            },
            "registrations": last_7_days,
        }

    return cache_get_or_set(
        "security.admin_overview",
        timeout=settings.API_CACHE_TTL_SECONDS,
        builder=builder,
    )
