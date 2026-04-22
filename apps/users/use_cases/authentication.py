import logging
import base64
from io import BytesIO

import pyotp
import qrcode
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.events import publish_event
from apps.security.email_token import email_verification_token
from apps.security.models import TrustedIP
from apps.security.services import (
    AttackDetectionService,
    SecurityAnalyticsService,
    is_account_locked,
    register_failed_attempt,
    reset_attempts,
)
from apps.security.threat_engine import ThreatEngine
from apps.security.tokens import password_reset_token
from apps.security.utils import (
    alert_on_repeated_security_events,
    get_client_ip,
    log_security_event,
)
from apps.users.models import DeviceSession, LoginHistory
from apps.users.serializers import UserSerializer
from apps.users.services.emails import (
    dispatch_password_reset_email,
    dispatch_verification_email,
)
from apps.users.services.authentication import (
    create_device_session,
    create_runtime_session,
    device_name,
    lock_user_after_failure,
    reset_user_lock_state,
    revoke_device_sessions,
    revoke_runtime_sessions,
    session_expiry_from_refresh_token,
)


User = get_user_model()
logger = logging.getLogger(__name__)


def register_user(serializer):
    user = serializer.save()
    verification_email_sent = dispatch_verification_email(user)
    message = (
        "User registered successfully. Please verify your email."
        if verification_email_sent
        else (
            "User registered successfully, but we could not send the verification "
            "email right now. Please request another verification email before signing in."
        )
    )
    return (
        {
            "message": message,
            "email_verification_required": True,
            "verification_email_sent": verification_email_sent,
            "email": user.email,
        },
        status.HTTP_201_CREATED,
    )

def verify_email(uid, token):
    if not uid or not token:
        return {"error": "Invalid verification link"}, 400

    try:
        user_id = int(force_str(urlsafe_base64_decode(uid)))
        user = User.objects.get(pk=user_id)
    except Exception:
        return {"error": "Invalid verification link"}, 400

    if not email_verification_token.check_token(user, token):
        return {"error": "Invalid or expired token"}, 400

    if user.email_verified:
        return {"message": "Email already verified"}, 200

    user.email_verified = True
    user.save(update_fields=["email_verified"])

    return {"message": "Email verified successfully"}, 200
def resend_verification_email(email):
    user = User.objects.filter(email=email).first()
    verification_email_sent = False
    if user and not user.email_verified:
        verification_email_sent = dispatch_verification_email(user)
        if verification_email_sent:
            message = "If the account exists, a verification email was sent."
        else:
            message = (
                "If the account exists, we could not send the verification email "
                "right now. Please try again shortly."
            )
        return {"message": message}, status.HTTP_200_OK
    return (
        {"message": "If the account exists, a verification email was sent."},
        status.HTTP_200_OK,
    )


def _finalize_login(request, user):
    ip_address = get_client_ip(request) or "127.0.0.1"
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    device = device_name(user_agent)
    refresh = RefreshToken.for_user(user)

    reset_attempts(user.email, ip_address)
    reset_user_lock_state(user)
    ThreatEngine.record_successful_login(ip_address)
    AttackDetectionService.check_and_block_ip(ip_address)

    LoginHistory.objects.create(user=user, ip_address=ip_address, user_agent=user_agent)
    create_device_session(
        user,
        str(refresh),
        device=device,
        ip_address=ip_address,
        trusted=True,
    )
    create_runtime_session(
        user,
        ip_address=ip_address,
        user_agent=user_agent,
        device=device,
    )

    log_security_event(user=user, event_type="LOGIN_SUCCESS", request=request)
    publish_event(
        "user.login_succeeded",
        payload={"user_id": user.id, "ip_address": ip_address, "device": device},
    )
    return {
        "user": UserSerializer(user).data,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }, status.HTTP_200_OK


def can_login(self):
    if self.is_superuser:
        return True
    return self.is_active and getattr(self, "email_verified", True)

def login_user(request, *, email, password):
    ip_address = get_client_ip(request) or "127.0.0.1"
    user_agent = request.META.get("HTTP_USER_AGENT", "")

    if ThreatEngine.is_blocked(ip_address):
        if not TrustedIP.objects.filter(ip_address=ip_address).exists():
            return {"error": "IP blocked. Try again later"}, status.HTTP_403_FORBIDDEN

    if not ThreatEngine.check_rate_limit(ip_address):
        return {"error": "Too many requests"}, status.HTTP_429_TOO_MANY_REQUESTS

    if is_account_locked(email, ip_address):
        return (
            {"error": "Too many failed login attempts. Try again later."},
            status.HTTP_403_FORBIDDEN,
        )
    

    
    
    

    candidate = User.objects.filter(email=email).first()
    if candidate and candidate.account_locked_until and candidate.account_locked_until > timezone.now():
        return {"error": "Account locked. Try again later."}, status.HTTP_403_FORBIDDEN

    user = authenticate(request, email=email, password=password)
    SecurityAnalyticsService.record_login_attempt(
        email=email,
        ip_address=ip_address,
        user_agent=user_agent,
        success=bool(user),
    )

    if user is None:
        register_failed_attempt(email, ip_address)
        ThreatEngine.record_failed_login(ip_address)
        locked = lock_user_after_failure(candidate)
        log_security_event(
            user=None,
            event_type="LOGIN_FAILED",
            request=request,
            metadata={"email": email},
        )
        return (
            {
                "error": (
                    "Account locked. Try again later."
                    if locked
                    else "Invalid credentials"
                )
            },
            status.HTTP_403_FORBIDDEN if locked else status.HTTP_401_UNAUTHORIZED,
        )

    if not user.email_verified and not user.is_superuser:
        return (
            {
                "error": "Please verify your email before logging in.",
                "email_verification_required": True,
            },
            status.HTTP_403_FORBIDDEN,
        )

    if not user.is_active:
        return {"error": "Account disabled"}, status.HTTP_403_FORBIDDEN

    if user.two_factor_enabled:
        return {"message": "2FA required", "user_id": user.id}, status.HTTP_200_OK
    

    if not user.can_login():
        return {"error": "Access denied"}, 403

    return _finalize_login(request, user)


   


def logout_user(*, user, refresh_token):
    if not refresh_token:
        return {"detail": "Refresh token is required."}, status.HTTP_400_BAD_REQUEST

    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except Exception:
        return {"detail": "Invalid token."}, status.HTTP_400_BAD_REQUEST

    session = DeviceSession.objects.filter(
        user=user,
        refresh_token_hash=DeviceSession.build_refresh_token_hash(refresh_token),
        is_active=True,
    ).first()
    if session:
        session.revoke("User logout")
        session.save(update_fields=["is_active", "revoked_at", "revoked_reason"])

    return {"detail": "Successfully logged out."}, status.HTTP_205_RESET_CONTENT


def request_password_reset(request, *, email):
    user = User.objects.filter(email=email).first()
    ip_address = get_client_ip(request)

    log_security_event(
        user=user,
        event_type="PASSWORD_RESET_REQUESTED",
        request=request,
        metadata={"email": email},
    )
    alert_on_repeated_security_events(
        "PASSWORD_RESET_REQUESTED",
        user=user,
        ip=ip_address,
        threshold=3,
        window_minutes=60,
        title="Repeated password reset requests",
        message="Multiple password reset requests were detected in a short period.",
        severity="high",
    )
    if user:
        reset_email_sent = dispatch_password_reset_email(user)
        if not reset_email_sent:
            logger.warning(
                "Password reset email could not be dispatched",
                extra={"user_id": user.id, "email": user.email},
            )
    return {"message": "If the email exists, a reset link was sent."}, status.HTTP_200_OK


def reset_password(request, *, uid, token, new_password):
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        log_security_event(
            user=None,
            event_type="PASSWORD_RESET_FAILED",
            request=request,
            metadata={"reason": "invalid_uid"},
        )
        return {"error": "Invalid UID"}, status.HTTP_400_BAD_REQUEST

    if not password_reset_token.check_token(user, token):
        log_security_event(
            user=user,
            event_type="PASSWORD_RESET_FAILED",
            request=request,
            metadata={"reason": "invalid_token"},
        )
        alert_on_repeated_security_events(
            "PASSWORD_RESET_FAILED",
            user=user,
            ip=get_client_ip(request),
            threshold=3,
            window_minutes=30,
            title="Repeated invalid password reset attempts",
            message="Multiple invalid password reset attempts were detected.",
            severity="high",
        )
        return {"error": "Invalid or expired token"}, status.HTTP_400_BAD_REQUEST

    user.set_password(new_password)
    reset_user_lock_state(user)
    user.save()
    revoke_device_sessions(user, reason="Password reset completed")
    revoke_runtime_sessions(user)
    log_security_event(user=user, event_type="PASSWORD_RESET_COMPLETED", request=request)
    return {"message": "Password reset successful"}, status.HTTP_200_OK


def setup_two_factor(user):
    secret = pyotp.random_base32()
    user.two_factor_secret = secret
    user.save(update_fields=["two_factor_secret"])
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=user.email, issuer_name="Backend API")
    qr = qrcode.make(uri)
    buffer = BytesIO()
    qr.save(buffer)
    return {
        "qr_code": base64.b64encode(buffer.getvalue()).decode(),
        "secret": secret,
    }, status.HTTP_200_OK


def verify_two_factor_setup(request, *, user, otp):
    if not user.two_factor_secret:
        return {"error": "2FA is not set up."}, status.HTTP_400_BAD_REQUEST

    if not pyotp.TOTP(user.two_factor_secret).verify(otp):
        log_security_event(user=user, event_type="2FA_FAILED", request=request)
        alert_on_repeated_security_events(
            "2FA_FAILED",
            user=user,
            ip=get_client_ip(request),
            threshold=5,
            window_minutes=10,
            title="Repeated failed 2FA verification",
            message="Multiple failed 2FA verification attempts were detected.",
            severity="high",
        )
        return {"error": "Invalid OTP"}, status.HTTP_400_BAD_REQUEST

    user.two_factor_enabled = True
    user.save(update_fields=["two_factor_enabled"])
    log_security_event(user=user, event_type="2FA_ENABLED", request=request)
    return {"message": "2FA enabled successfully"}, status.HTTP_200_OK


def verify_two_factor_login(request, *, user_id, otp):
    user = User.objects.filter(id=user_id).first()
    if not user or not user.two_factor_secret:
        return {"error": "User not found"}, status.HTTP_404_NOT_FOUND

    if not pyotp.TOTP(user.two_factor_secret).verify(otp):
        log_security_event(user=user, event_type="2FA_FAILED", request=request)
        alert_on_repeated_security_events(
            "2FA_FAILED",
            user=user,
            ip=get_client_ip(request),
            threshold=5,
            window_minutes=10,
            title="Repeated failed 2FA login",
            message="Multiple failed 2FA login attempts were detected.",
            severity="high",
        )
        return {"error": "Invalid OTP"}, status.HTTP_400_BAD_REQUEST

    return _finalize_login(request, user)


def refresh_device_session(request, *, refresh_token, refresh_response):
    if not refresh_token:
        return {"detail": "Refresh token is required."}, status.HTTP_400_BAD_REQUEST

    session = DeviceSession.objects.filter(
        refresh_token_hash=DeviceSession.build_refresh_token_hash(refresh_token),
        is_active=True,
        revoked_at__isnull=True,
    ).first()
    if not session:
        return {"detail": "Refresh token not recognized."}, status.HTTP_401_UNAUTHORIZED

    if session.expires_at and session.expires_at <= timezone.now():
        session.revoke("Refresh token expired")
        session.save(update_fields=["is_active", "revoked_at", "revoked_reason"])
        return {"detail": "Refresh token expired."}, status.HTTP_401_UNAUTHORIZED

    if refresh_response.status_code != status.HTTP_200_OK:
        return refresh_response.data, refresh_response.status_code

    new_refresh = refresh_response.data.get("refresh")
    if new_refresh:
        session.set_refresh_token(new_refresh)
        session.expires_at = session_expiry_from_refresh_token(new_refresh)
        session.last_rotated_at = timezone.now()
        session.save(
            update_fields=[
                "refresh_token",
                "refresh_token_hash",
                "refresh_token_last4",
                "expires_at",
                "last_rotated_at",
                "last_used",
            ]
        )

    log_security_event(
        user=session.user,
        event_type="TOKEN_REFRESHED",
        request=request,
        metadata={"session_id": str(session.id), "device": session.device},
    )
    return refresh_response.data, refresh_response.status_code
