from django.http import JsonResponse
from django.utils.cache import patch_cache_control

from apps.security.threat_engine import ThreatEngine
from apps.security.utils import get_client_ip


LOCAL_IPS = {"127.0.0.1", "::1", "localhost"}


class BlockIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = get_client_ip(request)

        if ip in LOCAL_IPS:
            return self.get_response(request)

        user = getattr(request, "user", None)
        if user and user.is_authenticated and user.is_staff:
            return self.get_response(request)

        if ip and ThreatEngine.is_blocked(ip):
            return JsonResponse(
                {"error": "Your IP has been temporarily blocked."},
                status=403,
            )

        return self.get_response(request)


class SmartSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = get_client_ip(request)
        if ip in LOCAL_IPS:
            return self.get_response(request)

        if ip and ThreatEngine.is_blocked(ip):
            return JsonResponse(
                {"error": "Blocked due to suspicious activity."},
                status=403,
            )

        if ip:
            activity = ThreatEngine.update_request(ip)
            score = ThreatEngine.calculate_risk(activity)
            ThreatEngine.enforce(ip, score)

        return self.get_response(request)


class SecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = get_client_ip(request)

        if request.path.startswith("/admin"):
            return self.get_response(request)

        if ip and ThreatEngine.is_blocked(ip):
            return JsonResponse(
                {"error": "Your IP is temporarily blocked."},
                status=403,
            )

        return self.get_response(request)


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault("X-Content-Type-Options", "nosniff")
        response.setdefault("Referrer-Policy", "same-origin")
        response.setdefault("X-Frame-Options", "DENY")
        response.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        response.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.setdefault("Cross-Origin-Resource-Policy", "same-origin")

        if request.path.startswith("/api/v1/auth/") or request.path.startswith("/api/v1/users/"):
            patch_cache_control(response, no_cache=True, no_store=True, must_revalidate=True, private=True)
            response.setdefault("Pragma", "no-cache")

        return response
