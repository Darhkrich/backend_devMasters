from django.db.models import Count

from apps.security.models import BlockedIP, SecurityAlert
from apps.users.models import LoginAttempt, User


def suspicious_logins(limit=50):
    attempts = LoginAttempt.objects.filter(success=False).order_by("-created_at")[:limit]
    return [
        {
            "email": attempt.email,
            "ip": attempt.ip_address,
            "device": attempt.user_agent,
            "time": attempt.created_at,
        }
        for attempt in attempts
    ]


def top_attacking_ips(limit=10):
    attackers = (
        LoginAttempt.objects.filter(success=False)
        .values("ip_address")
        .annotate(attempts=Count("id"))
        .order_by("-attempts")[:limit]
    )
    return list(attackers)


def unlock_user_account(user_id):
    user = User.objects.filter(id=user_id).first()
    if not user:
        return None

    user.account_locked_until = None
    user.failed_login_attempts = 0
    user.save(update_fields=["account_locked_until", "failed_login_attempts"])
    return user


def blocked_ip_list():
    return [
        {
            "ip": blocked_ip.ip_address,
            "reason": blocked_ip.reason,
            "blocked_at": blocked_ip.created_at,
            "blocked_until": blocked_ip.blocked_until,
            "is_active": blocked_ip.is_active,
        }
        for blocked_ip in BlockedIP.objects.all().order_by("-created_at")
    ]


def unblock_ip(ip):
    deleted, _ = BlockedIP.objects.filter(ip_address=ip).delete()
    return deleted > 0


def resolve_security_alert(alert_id, user):
    alert = SecurityAlert.objects.filter(id=alert_id, user=user).first()
    if not alert:
        return None

    alert.resolved = True
    alert.save(update_fields=["resolved"])
    return alert
