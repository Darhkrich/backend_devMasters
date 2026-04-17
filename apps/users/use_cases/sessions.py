from rest_framework import status

from apps.security.models import UserSession
from apps.security.utils import log_security_event
from apps.users.models import DeviceSession
from apps.users.serializers import DeviceSessionSerializer


def active_runtime_sessions(user):
    sessions = UserSession.objects.filter(user=user, is_active=True)
    return [
        {
            "id": session.id,
            "ip": session.ip_address,
            "device": session.device,
            "created_at": session.created_at,
            "last_seen": session.last_seen,
        }
        for session in sessions
    ]


def active_device_sessions(user):
    sessions = DeviceSession.objects.filter(user=user, is_active=True)
    return DeviceSessionSerializer(sessions, many=True).data


def revoke_device_session(request, *, user, session_id):
    session = DeviceSession.objects.filter(id=session_id, user=user).first()
    if not session:
        return {"error": "Session not found"}, status.HTTP_404_NOT_FOUND

    session.revoke("User revoked device session")
    session.save(update_fields=["is_active", "revoked_at", "revoked_reason"])
    log_security_event(
        user=user,
        event_type="SESSION_REVOKED",
        request=request,
        metadata={"session_id": str(session_id)},
    )
    return {"message": "Device session revoked"}, status.HTTP_200_OK
