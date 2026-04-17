from rest_framework import status

from apps.core.events import publish_event
from apps.security.utils import log_security_event
from apps.users.models import SecurityEvent, User
from apps.users.serializers import LoginHistorySerializer, SecurityEventSerializer
from apps.users.services.authentication import (
    reset_user_lock_state,
    revoke_device_sessions,
    revoke_runtime_sessions,
)
from apps.users.services.emails import send_verification_email


def delete_account(user):
    revoke_device_sessions(user, reason="Account deleted")
    revoke_runtime_sessions(user)
    user.delete()
    return {"message": "Account deleted successfully"}, status.HTTP_204_NO_CONTENT


def change_password(request, *, user, old_password, new_password):
    if not user.check_password(old_password):
        return {"error": "Old password is incorrect"}, status.HTTP_400_BAD_REQUEST

    user.set_password(new_password)
    reset_user_lock_state(user)
    user.save()
    revoke_device_sessions(user, reason="Password changed")
    revoke_runtime_sessions(user)
    log_security_event(user=user, event_type="PASSWORD_CHANGED", request=request)
    publish_event("user.password_changed", payload={"user_id": user.id})
    return {"message": "Password updated successfully"}, status.HTTP_200_OK


def change_email(request, *, user, new_email):
    if User.objects.filter(email=new_email).exclude(id=user.id).exists():
        return {"error": "Email is already in use."}, status.HTTP_400_BAD_REQUEST

    user.email = new_email
    user.email_verified = False
    user.save(update_fields=["email", "email_verified"])
    log_security_event(
        user=user,
        event_type="EMAIL_CHANGED",
        request=request,
        metadata={"new_email": new_email},
    )
    send_verification_email(user)
    return {"message": "Email updated. Please verify your new email."}, status.HTTP_200_OK


def login_history_for_user(user):
    history = user.login_history.all()[:20]
    return LoginHistorySerializer(history, many=True).data


def security_events_for_user(user):
    events = SecurityEvent.objects.filter(user=user)[:30]
    return SecurityEventSerializer(events, many=True).data
