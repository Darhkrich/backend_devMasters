from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.use_cases.sessions import (
    active_device_sessions,
    active_runtime_sessions,
    revoke_device_session,
)

from ...throttles import SensitiveUserActionThrottle


class UserSessionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(active_runtime_sessions(request.user))


class DeviceSessionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(active_device_sessions(request.user))


class RevokeDeviceSessionView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [SensitiveUserActionThrottle]

    def post(self, request):
        payload, status_code = revoke_device_session(
            request,
            user=request.user,
            session_id=request.data.get("session_id"),
        )
        return Response(payload, status=status_code)
