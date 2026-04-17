from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditLog
from apps.core.permissions import IsAdminUserCustom


class AuditLogsView(APIView):
    permission_classes = [IsAdminUserCustom]

    def get(self, request):
        logs = AuditLog.objects.select_related("user")[:100]
        return Response(
            [
                {
                    "id": log.id,
                    "action": log.action,
                    "user": log.user.email if log.user else None,
                    "method": log.method,
                    "path": log.path,
                    "status_code": log.status_code,
                    "ip_address": log.ip_address,
                    "timestamp": log.timestamp,
                }
                for log in logs
            ]
        )
