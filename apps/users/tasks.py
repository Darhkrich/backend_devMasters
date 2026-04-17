from django.contrib.auth import get_user_model

from apps.core.tasks import register_task
from apps.users.services.emails import send_password_reset_email, send_verification_email


User = get_user_model()


@register_task("users.send_verification_email")
def send_verification_email_task(*, user_id):
    user = User.objects.filter(id=user_id).first()
    if user:
        send_verification_email(user)


@register_task("users.send_password_reset_email")
def send_password_reset_email_task(*, user_id):
    user = User.objects.filter(id=user_id).first()
    if user:
        send_password_reset_email(user)
