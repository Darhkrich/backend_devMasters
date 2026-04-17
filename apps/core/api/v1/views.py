from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.observability import metrics_snapshot
from apps.core.permissions import InternalMetricsPermission


class APIVersionsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "default": settings.API_DEFAULT_VERSION,
                "supported": settings.API_SUPPORTED_VERSIONS,
                "deprecated": settings.API_DEPRECATED_VERSIONS,
                "deprecation_policy_url": settings.API_DEPRECATION_POLICY_URL,
            }
        )


class MetricsView(APIView):
    permission_classes = [InternalMetricsPermission]

    def get(self, request):
        return Response(metrics_snapshot())


class LivenessView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok", "time": timezone.now()})


class ReadinessView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        checks = {"database": "ok", "cache": "ok"}
        status_code = 200

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            checks["database"] = "error"
            status_code = 503

        cache_key = "health:ready"
        try:
            cache.set(cache_key, "ok", 5)
            if cache.get(cache_key) != "ok":
                raise RuntimeError("cache round-trip failed")
            cache.delete(cache_key)
        except Exception:
            checks["cache"] = "error"
            status_code = 503

        overall = "ok" if status_code == 200 else "degraded"
        return Response(
            {
                "status": overall,
                "environment": settings.APP_ENV,
                "checks": checks,
            },
            status=status_code,
        )
