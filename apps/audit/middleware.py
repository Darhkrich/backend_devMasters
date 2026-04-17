import time

from django.utils.deprecation import MiddlewareMixin

from apps.audit.models import AuditLog
from apps.security.utils import get_client_ip


class AuditRequestMiddleware(MiddlewareMixin):

    def process_request(self, request):
        request.start_time = time.time()

    def process_response(self, request, response):

        # Ignore static and media files
        if request.path.startswith("/static/") or request.path.startswith("/media/"):
            return response

        try:
            start_time = getattr(request, "start_time", None)

            if start_time:
                response_time = int((time.time() - start_time) * 1000)
            else:
                response_time = None

            user = getattr(request, "user", None)
            if user and user.is_authenticated:
                user = user
            else:
                user = None

            ip = get_client_ip(request)
            action = "VIEW" if request.path.startswith("/admin") else "REQUEST"

            AuditLog.objects.create(
                user=user,
                action=action,
                method=request.method,
                path=request.path,
                status_code=response.status_code,
                ip_address=ip,
                response_time=response_time,
            )

        except Exception:
            pass

        return response
