from apps.core.events import register_event_handler
from apps.core.tasks import enqueue_task


@register_event_handler("user.registered")
def handle_user_registered(payload):
    enqueue_task("users.send_verification_email", user_id=payload["user_id"])


@register_event_handler("user.email_changed")
def handle_user_email_changed(payload):
    enqueue_task("users.send_verification_email", user_id=payload["user_id"])


@register_event_handler("user.password_reset_requested")
def handle_password_reset_requested(payload):
    enqueue_task("users.send_password_reset_email", user_id=payload["user_id"])
