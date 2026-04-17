from django.middleware.csrf import CsrfViewMiddleware
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(BaseAuthentication):
    """
    Authenticate API requests with the JWT access token stored in a cookie.
    Cookie-authenticated unsafe requests must also pass Django's CSRF check.
    """

    def __init__(self):
        self.jwt_authentication = JWTAuthentication()

    def authenticate(self, request):
        access_token = request.COOKIES.get("access_token")
        if not access_token:
            return None

        try:
            validated_token = self.jwt_authentication.get_validated_token(access_token)
            self._enforce_csrf(request)
            user = self.jwt_authentication.get_user(validated_token)
        except exceptions.AuthenticationFailed:
            # Stale/invalid cookies should not block public endpoints such as login.
            # Protected endpoints will still fail later via permission checks.
            return None
        except exceptions.PermissionDenied:
            raise
        except Exception as exc:
            raise exceptions.AuthenticationFailed("Invalid token.") from exc

        return user, validated_token

    def authenticate_header(self, request):
        return "Bearer"

    def _enforce_csrf(self, request):
        check = CsrfViewMiddleware(lambda req: None)
        check.process_request(request)
        reason = check.process_view(request, None, (), {})
        if reason:
            raise exceptions.PermissionDenied(f"CSRF Failed: {reason}")
