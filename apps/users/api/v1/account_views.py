from django.conf import settings
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers import (
    ChangeEmailSerializer,
    ChangePasswordSerializer,
    UserProfileSerializer,
    UserSerializer,
)
from apps.users.use_cases.account import (
    change_email,
    change_password,
    delete_account,
    login_history_for_user,
    security_events_for_user,
)

from ...throttles import SensitiveUserActionThrottle


def set_csrf_cookie(response, request):
    csrf_token = get_token(request)
    response.set_cookie(
        settings.CSRF_COOKIE_NAME,
        csrf_token,
        max_age=settings.CSRF_COOKIE_AGE,
        domain=settings.CSRF_COOKIE_DOMAIN,
        path=settings.CSRF_COOKIE_PATH,
        secure=getattr(settings, "CSRF_COOKIE_SECURE", False),
        httponly=settings.CSRF_COOKIE_HTTPONLY,
        samesite=settings.CSRF_COOKIE_SAMESITE,
    )
    response["X-CSRFToken"] = csrf_token
    return response


def clear_auth_cookies(response):
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
    response.delete_cookie("boem_session")
    response.delete_cookie("boem_role")
    return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        response = Response(UserSerializer(request.user).data)
        return set_csrf_cookie(response, request)

    def patch(self, request):
        data = {
            key: value
            for key, value in request.data.items()
            if key in {"first_name", "last_name"}
        }
        serializer = UserSerializer(
            request.user,
            data=data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)

    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request):
        payload, status_code = delete_account(request.user)
        response = Response(payload, status=status_code)
        return clear_auth_cookies(response)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [SensitiveUserActionThrottle]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload, status_code = change_password(
            request,
            user=request.user,
            old_password=serializer.validated_data["old_password"],
            new_password=serializer.validated_data["new_password"],
        )
        return Response(payload, status=status_code)


class ChangeEmailView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [SensitiveUserActionThrottle]

    def post(self, request):
        serializer = ChangeEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload, status_code = change_email(
            request,
            user=request.user,
            new_email=serializer.validated_data["new_email"],
        )
        return Response(payload, status=status_code)


class LoginHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(login_history_for_user(request.user))


class SecurityEventsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(security_events_for_user(request.user))
