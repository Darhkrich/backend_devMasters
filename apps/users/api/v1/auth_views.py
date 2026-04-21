from django.conf import settings
from django.contrib.auth import get_user_model
from django.middleware.csrf import CsrfViewMiddleware, get_token
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.audit.utils import log_action
from apps.security.email_token import email_verification_token
from apps.users.models import DeviceSession
from apps.users.serializers import LoginSerializer, RegisterSerializer, ResetPasswordSerializer
from apps.users.use_cases.authentication import (
    login_user,
    logout_user,
    refresh_device_session,
    register_user,
    request_password_reset,
    resend_verification_email,
    reset_password,
    setup_two_factor,
    verify_two_factor_login,
    verify_two_factor_setup,
)

from ...throttles import (
    LoginRateThrottle,
    PasswordResetRateThrottle,
    RegisterRateThrottle,
    ResendVerificationRateThrottle,
    SensitiveUserActionThrottle,
    TokenRefreshRateThrottle,
    TwoFactorRateThrottle,
)


User = get_user_model()


def _csrf_cookie_kwargs(max_age):
    return {
        "max_age": max_age,
        "domain": settings.CSRF_COOKIE_DOMAIN,
        "path": settings.CSRF_COOKIE_PATH,
        "secure": getattr(settings, "CSRF_COOKIE_SECURE", False),
        "httponly": settings.CSRF_COOKIE_HTTPONLY,
        "samesite": settings.CSRF_COOKIE_SAMESITE,
    }


def _auth_cookie_kwargs(max_age):
    return {
        "httponly": True,
        "secure": getattr(settings, "AUTH_COOKIE_SECURE", not settings.DEBUG),
        "samesite": getattr(settings, "AUTH_COOKIE_SAMESITE", "Lax"),
        "domain": getattr(settings, "AUTH_COOKIE_DOMAIN", None),
        "path": getattr(settings, "AUTH_COOKIE_PATH", "/"),
        "max_age": max_age,
    }


def _session_max_age_for_user(user):
    return None if user.is_staff else 30 * 24 * 60 * 60


def _set_csrf_cookie(response, request, *, max_age):
    csrf_token = get_token(request)
    response.set_cookie(
        settings.CSRF_COOKIE_NAME,
        csrf_token,
        **_csrf_cookie_kwargs(max_age),
    )
    response["X-CSRFToken"] = csrf_token
    return response


def _clear_auth_cookies(response):
    response.delete_cookie(
        "access_token",
        path=getattr(settings, "AUTH_COOKIE_PATH", "/"),
        domain=getattr(settings, "AUTH_COOKIE_DOMAIN", None),
        samesite=getattr(settings, "AUTH_COOKIE_SAMESITE", "Lax"),
    )
    response.delete_cookie(
        "refresh_token",
        path=getattr(settings, "AUTH_COOKIE_PATH", "/"),
        domain=getattr(settings, "AUTH_COOKIE_DOMAIN", None),
        samesite=getattr(settings, "AUTH_COOKIE_SAMESITE", "Lax"),
    )
    response.delete_cookie(
        settings.CSRF_COOKIE_NAME,
        path=settings.CSRF_COOKIE_PATH,
        domain=settings.CSRF_COOKIE_DOMAIN,
        samesite=settings.CSRF_COOKIE_SAMESITE,
    )
    return response


def _set_auth_cookies(response, request, *, user, access, refresh):
    max_age = _session_max_age_for_user(user)
    response.set_cookie("access_token", access, **_auth_cookie_kwargs(max_age))
    response.set_cookie("refresh_token", refresh, **_auth_cookie_kwargs(max_age))
    return _set_csrf_cookie(response, request, max_age=max_age)


def _strip_token_payload(payload):
    sanitized = dict(payload)
    sanitized.pop("access", None)
    sanitized.pop("refresh", None)
    return sanitized


def _enforce_csrf(request):
    check = CsrfViewMiddleware(lambda req: None)
    check.process_request(request)
    reason = check.process_view(request, None, (), {})
    if reason:
        return Response({"detail": f"CSRF Failed: {reason}"}, status=status.HTTP_403_FORBIDDEN)
    return None


class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    throttle_classes = [RegisterRateThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload, status_code = register_user(serializer)
        return Response(payload, status=status_code)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        uidb64 = request.GET.get("uid")
        token = request.GET.get("token")

        if not uidb64 or not token:
            return Response({"error": "Invalid verification link"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": "Invalid user"}, status=status.HTTP_400_BAD_REQUEST)

        if not email_verification_token.check_token(user, token):
            return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

        if user.email_verified:
            return Response({"message": "Email already verified"}, status=status.HTTP_200_OK)

        user.email_verified = True
        user.save(update_fields=["email_verified"])
        return Response({"message": "Email verified successfully"}, status=status.HTTP_200_OK)


class ResendVerificationEmailView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ResendVerificationRateThrottle]

    def post(self, request):
        email = (request.data.get("email") or "").lower().strip()
        payload, status_code = resend_verification_email(email)
        return Response(payload, status=status_code)


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload, status_code = login_user(
            request,
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        response = Response(payload, status=status_code)

        if status_code == status.HTTP_200_OK and payload.get("access") and payload.get("refresh") and payload.get("user"):
            user = User.objects.get(pk=payload["user"]["id"])
            _set_auth_cookies(
                response,
                request,
                user=user,
                access=payload["access"],
                refresh=payload["refresh"],
            )
            response.data = _strip_token_payload(payload)

        return response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [SensitiveUserActionThrottle]

    def post(self, request):
        refresh_token = request.data.get("refresh") or request.COOKIES.get("refresh_token")
        payload, status_code = logout_user(
            user=request.user,
            refresh_token=refresh_token,
        )
        log_action(
            user=request.user,
            action="LOGOUT",
            model_name="User",
            object_id=request.user.id,
            request=request,
        )
        response = Response(payload, status=status_code)
        return _clear_auth_cookies(response)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request):
        email = (request.data.get("email") or "").lower().strip()
        payload, status_code = request_password_reset(request, email=email)
        return Response(payload, status=status_code)


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload, status_code = reset_password(
            request,
            uid=serializer.validated_data["uid"],
            token=serializer.validated_data["token"],
            new_password=serializer.validated_data["new_password"],
        )
        return Response(payload, status=status_code)


class Setup2FAView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [SensitiveUserActionThrottle]

    def post(self, request):
        payload, status_code = setup_two_factor(request.user)
        return Response(payload, status=status_code)


class Verify2FAView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [TwoFactorRateThrottle]

    def post(self, request):
        payload, status_code = verify_two_factor_setup(
            request,
            user=request.user,
            otp=request.data.get("otp"),
        )
        return Response(payload, status=status_code)


class Verify2FALoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [TwoFactorRateThrottle]

    def post(self, request):
        payload, status_code = verify_two_factor_login(
            request,
            user_id=request.data.get("user_id"),
            otp=request.data.get("otp"),
        )
        response = Response(payload, status=status_code)

        if status_code == status.HTTP_200_OK and payload.get("access") and payload.get("refresh") and payload.get("user"):
            user = User.objects.get(pk=payload["user"]["id"])
            _set_auth_cookies(
                response,
                request,
                user=user,
                access=payload["access"],
                refresh=payload["refresh"],
            )
            response.data = _strip_token_payload(payload)

        return response


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code != status.HTTP_200_OK:
            return response

        access = response.data.get("access")
        refresh = response.data.get("refresh")
        if not access or not refresh:
            return response

        user_id = AccessToken(access).payload.get("user_id")
        user = User.objects.get(pk=user_id)
        _set_auth_cookies(
            response,
            request,
            user=user,
            access=access,
            refresh=refresh,
        )
        response.data = {"detail": "Login successful"}
        return response


class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
    throttle_classes = [TokenRefreshRateThrottle]
    serializer_class = TokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh") or request.COOKIES.get("refresh_token")
        if request.COOKIES.get("refresh_token"):
            csrf_failure = _enforce_csrf(request)
            if csrf_failure is not None:
                return csrf_failure

        session = None
        if refresh_token:
            session = DeviceSession.objects.filter(
                refresh_token_hash=DeviceSession.build_refresh_token_hash(refresh_token),
                is_active=True,
                revoked_at__isnull=True,
            ).select_related("user").first()

        serializer = self.get_serializer(data={"refresh": refresh_token})
        serializer.is_valid(raise_exception=True)
        refresh_response = Response(serializer.validated_data, status=status.HTTP_200_OK)
        payload, status_code = refresh_device_session(
            request,
            refresh_token=refresh_token,
            refresh_response=refresh_response,
        )

        response = Response(
            {"detail": "Session refreshed"} if status_code == status.HTTP_200_OK else payload,
            status=status_code,
        )

        if status_code != status.HTTP_200_OK:
            return _clear_auth_cookies(response)

        user = session.user if session else User.objects.get(pk=RefreshToken(refresh_token).payload.get("user_id"))
        _set_auth_cookies(
            response,
            request,
            user=user,
            access=payload["access"],
            refresh=payload.get("refresh") or refresh_token,
        )
        return response
