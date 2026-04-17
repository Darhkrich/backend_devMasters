import logging

from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from apps.core.observability import (
    clear_request_context,
    log_request_completed,
    new_request_context,
    record_request_metrics,
)

logger = logging.getLogger(__name__)


class GlobalExceptionMiddleware(MiddlewareMixin):

    def process_exception(self, request, exception):

        logger.exception("Unhandled exception on %s %s", request.method, request.path)

        return JsonResponse(
            {
                "error":
                "Internal Server Error: An unexpected error occurred."
                 
            },
            status=500,
        )


class APIVersioningMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if not request.path.startswith("/api/"):
            return response

        path_parts = [part for part in request.path.strip("/").split("/") if part]
        version = (
            path_parts[1]
            if len(path_parts) >= 2 and path_parts[0] == "api"
            else getattr(settings, "API_DEFAULT_VERSION", "v1")
        )
        response["X-API-Version"] = version

        deprecated_versions = getattr(settings, "API_DEPRECATED_VERSIONS", {})
        if version in deprecated_versions:
            details = deprecated_versions[version]
            response["Deprecation"] = "true"
            if details.get("sunset"):
                response["Sunset"] = details["sunset"]
            if details.get("policy_url"):
                response["Link"] = f'<{details["policy_url"]}>; rel="deprecation"'

        return response


class RequestTracingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        new_request_context(request)

    def process_response(self, request, response):
        request_id = getattr(request, "request_id", None)
        trace_id = getattr(request, "trace_id", None)
        if request_id:
            response["X-Request-ID"] = request_id
        if trace_id:
            response["X-Trace-ID"] = trace_id

        duration_ms = record_request_metrics(request, response)
        log_request_completed(request, response, duration_ms)
        clear_request_context()
        return response

    def process_exception(self, request, exception):
        clear_request_context()




class CoepMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Allow images to be loaded by your Next.js app
        response["Cross-Origin-Resource-Policy"] = "cross-origin"
        return response
