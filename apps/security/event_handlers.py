from apps.core.events import register_event_handler
from apps.core.tasks import enqueue_task


@register_event_handler("user.login_succeeded")
def handle_user_login_succeeded(payload):
    enqueue_task(
        "security.process_successful_login",
        user_id=payload["user_id"],
        ip_address=payload["ip_address"],
        device=payload["device"],
    )


@register_event_handler("user.password_changed")
def handle_user_password_changed(payload):
    enqueue_task("security.send_password_changed_alert", user_id=payload["user_id"])
