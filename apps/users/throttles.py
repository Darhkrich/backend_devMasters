from rest_framework.throttling import SimpleRateThrottle


class UserOrIPRateThrottle(SimpleRateThrottle):
    scope = ""

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            return f"{self.scope}_user_{request.user.pk}"

        ident = self.get_ident(request)
        if not ident:
            return None
        return f"{self.scope}_ip_{ident}"


class LoginRateThrottle(SimpleRateThrottle):
    scope = "login"

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        email = (request.data.get("email", "") or "").lower().strip()
        if not ident:
            return None
        return f"login_{ident}_{email}"


class TokenRefreshRateThrottle(SimpleRateThrottle):
    scope = "token_refresh"

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        if not ident:
            return None
        return f"token_refresh_{ident}"


class RegisterRateThrottle(SimpleRateThrottle):
    scope = "register"

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        if not ident:
            return None
        return f"register_{ident}"


class PasswordResetRateThrottle(SimpleRateThrottle):
    scope = "password_reset"

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        email = (request.data.get("email", "") or "").lower().strip()
        if not ident:
            return None
        return f"password_reset_{ident}_{email}"


class ResendVerificationRateThrottle(SimpleRateThrottle):
    scope = "resend_verification"

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        email = (request.data.get("email", "") or "").lower().strip()
        if not ident:
            return None
        return f"verify_{ident}_{email}"


class TwoFactorRateThrottle(UserOrIPRateThrottle):
    scope = "two_factor"


class SensitiveUserActionThrottle(UserOrIPRateThrottle):
    scope = "sensitive_user_action"
