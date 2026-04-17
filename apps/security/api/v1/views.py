from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.security.analytics import (
    admin_dashboard_overview,
    admin_dashboard_stats,
    admin_security_dashboard,
    login_trend,
)
from apps.security.models import SecurityAlert
from apps.security.permissions import IsAdminUserRole, IsSecurityAdmin
from apps.security.throttles import AdminActionThrottle, SecurityAnalyticsThrottle
from apps.security.use_cases import (
    blocked_ip_list,
    resolve_security_alert,
    suspicious_logins,
    top_attacking_ips,
    unblock_ip,
    unlock_user_account,
)
from apps.security.utils import log_security_event
from apps.users.models import User


class AdminSecurityDashboardView(APIView):
    permission_classes = [IsAdminUserRole]
    throttle_classes = [SecurityAnalyticsThrottle]

    def get(self, request):
        return Response(admin_security_dashboard())


class SuspiciousLoginView(APIView):
    permission_classes = [IsAuthenticated, IsSecurityAdmin]
    throttle_classes = [SecurityAnalyticsThrottle]

    def get(self, request):
        return Response(suspicious_logins())


class TopAttackingIPsView(APIView):
    permission_classes = [IsAuthenticated, IsSecurityAdmin]
    throttle_classes = [SecurityAnalyticsThrottle]

    def get(self, request):
        return Response(top_attacking_ips())


class UnlockUserView(APIView):
    permission_classes = [IsAuthenticated, IsSecurityAdmin]
    throttle_classes = [AdminActionThrottle]

    def post(self, request):
        user_id = request.data.get("user_id")
        user = unlock_user_account(user_id)
        if not user:
            return Response({"error": "User not found"}, status=404)
        log_security_event(
            user=request.user,
            event_type="ADMIN_ACCESS",
            request=request,
            metadata={"action": "unlock_user", "target_user_id": user.id},
        )
        return Response({"message": "User account unlocked"})


class BlockedIPsView(APIView):
    permission_classes = [IsAuthenticated, IsSecurityAdmin]
    throttle_classes = [SecurityAnalyticsThrottle]

    def get(self, request):
        return Response(blocked_ip_list())


class UnblockIPView(APIView):
    permission_classes = [IsAuthenticated, IsSecurityAdmin]
    throttle_classes = [AdminActionThrottle]

    def post(self, request):
        ip = request.data.get("ip")
        if not unblock_ip(ip):
            return Response({"error": "IP not found"}, status=404)
        log_security_event(
            user=request.user,
            event_type="ADMIN_ACCESS",
            request=request,
            metadata={"action": "unblock_ip", "ip": ip},
        )
        return Response({"message": "IP unblocked"})


class LoginTrendView(APIView):
    permission_classes = [IsAdminUserRole]
    throttle_classes = [SecurityAnalyticsThrottle]

    def get(self, request):
        return Response(login_trend())


class AdminDashboardStatsView(APIView):
    permission_classes = [IsAdminUserRole]
    throttle_classes = [SecurityAnalyticsThrottle]

    def get(self, request):
        return Response(admin_dashboard_stats())


class AdminDashboardOverview(APIView):
    permission_classes = [IsAdminUserRole]
    throttle_classes = [SecurityAnalyticsThrottle]

    def get(self, request):
        return Response(admin_dashboard_overview())


class SecurityAlertsView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [SecurityAnalyticsThrottle]

    def get(self, request):
        alerts = SecurityAlert.objects.filter(user=request.user).order_by("-created_at")[:20]
        return Response(
            [
                {
                    "id": alert.id,
                    "title": alert.title,
                    "message": alert.message,
                    "severity": alert.severity,
                    "ip": alert.ip_address,
                    "created_at": alert.created_at,
                    "resolved": alert.resolved,
                }
                for alert in alerts
            ]
        )


class ResolveAlertView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [AdminActionThrottle]

    def post(self, request):
        alert_id = request.data.get("alert_id")
        alert = resolve_security_alert(alert_id, request.user)
        if not alert:
            return Response({"error": "Not found"}, status=404)
        return Response({"status": "resolved"})
