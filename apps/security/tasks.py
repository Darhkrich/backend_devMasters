from django.contrib.auth import get_user_model

from apps.core.tasks import register_task
from apps.security.services import DeviceDetectionService, SecurityEmailService
from apps.security.utils import detect_suspicious_login


User = get_user_model()


@register_task("security.process_successful_login")
def process_successful_login_task(*, user_id, ip_address, device):
    user = User.objects.filter(id=user_id).first()
    if user:
        detect_suspicious_login(user, ip_address, device)


@register_task("security.send_password_changed_alert")
def send_password_changed_alert_task(*, user_id):
    user = User.objects.filter(id=user_id).first()
    if user:
        SecurityEmailService.send_password_changed_alert(user)
