from rest_framework.throttling import SimpleRateThrottle


class AdminActionThrottle(SimpleRateThrottle):
    scope = "admin_action"

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            return f"admin_action_user_{request.user.pk}"

        ident = self.get_ident(request)
        if not ident:
            return None
        return f"admin_action_ip_{ident}"


class SecurityAnalyticsThrottle(SimpleRateThrottle):
    scope = "security_analytics"

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            return f"security_analytics_user_{request.user.pk}"

        ident = self.get_ident(request)
        if not ident:
            return None
        return f"security_analytics_ip_{ident}"
