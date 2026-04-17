import uuid
from datetime import datetime, timezone as dt_timezone

from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.security.models import UserSession
from apps.users.models import DeviceSession


def device_name(user_agent):
    if "Mobile" in user_agent:
        return "Mobile"
    if "Windows" in user_agent:
        return "Windows PC"
    if "Mac" in user_agent:
        return "Mac"
    if "Linux" in user_agent:
        return "Linux"
    return "Unknown"


def lock_user_after_failure(user):
    if not user:
        return False

    max_attempts = settings.SIMPLE_JWT.get("MAX_LOGIN_ATTEMPTS", 5)
    lock_time = settings.SIMPLE_JWT.get("LOGIN_LOCKOUT_TIME")

    user.failed_login_attempts += 1
    locked = False
    if user.failed_login_attempts >= max_attempts and lock_time:
        user.account_locked_until = timezone.now() + lock_time
        locked = True

    user.save(update_fields=["failed_login_attempts", "account_locked_until"])
    return locked


def reset_user_lock_state(user):
    user.failed_login_attempts = 0
    user.account_locked_until = None
    user.save(update_fields=["failed_login_attempts", "account_locked_until"])


def session_expiry_from_refresh_token(refresh_token):
    exp = RefreshToken(refresh_token).payload.get("exp")
    if not exp:
        return None
    return datetime.fromtimestamp(exp, tz=dt_timezone.utc)


def create_device_session(user, refresh_token, *, device, ip_address, trusted=False):
    session = DeviceSession(
        user=user,
        device=device,
        ip_address=ip_address,
        expires_at=session_expiry_from_refresh_token(refresh_token),
    )
    session.set_refresh_token(refresh_token)
    if trusted:
        session.mark_trusted()
    session.save()
    return session


def create_runtime_session(user, *, ip_address, user_agent, device):
    return UserSession.objects.create(
        user=user,
        session_id=str(uuid.uuid4()),
        ip_address=ip_address,
        user_agent=user_agent,
        device=device,
    )


def revoke_runtime_sessions(user):
    UserSession.objects.filter(user=user).update(is_active=False)


def revoke_device_sessions(user, *, reason):
    DeviceSession.objects.filter(user=user).update(
        is_active=False,
        revoked_reason=reason,
    )
