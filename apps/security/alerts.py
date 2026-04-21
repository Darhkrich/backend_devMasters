from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import SecurityAlert

class SecurityAlertService:

    @staticmethod
    def create_alert(title, message, severity="medium"):

        alert = SecurityAlert.objects.create(
            title=title,
            message=message,
            severity=severity
        )

        channel_layer = get_channel_layer()
        if channel_layer is None:
            return alert

        async_to_sync(channel_layer.group_send)(
            "security_events",
            {
                "type": "security_event",
                "data": {
                    "event": "security_alert",
                    "title": alert.title,
                    "message": alert.message,
                    "severity": alert.severity,
                    "time": alert.created_at.isoformat(),
                },
            },
        )

        return alert
