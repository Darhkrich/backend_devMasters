import logging
from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from apps.security.tokens import password_reset_token
from apps.security.email_token import email_verification_token



logger = logging.getLogger(__name__)


def frontend_url(path, **params):
    base_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000").rstrip("/")
    url = f"{base_url}{path}"
    if params:
        return f"{url}?{urlencode(params)}"
    return url


def _send_email(*, subject, text_body, html_body, recipient_list):
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipient_list,
    )
    message.attach_alternative(html_body, "text/html")

    try:
        sent_count = message.send(fail_silently=False)
    except Exception:
        logger.exception(
            "Failed to send email",
            extra={"recipients": recipient_list, "subject": subject},
        )
        raise

    if sent_count <= 0:
        raise RuntimeError(f"Email backend accepted zero recipients for subject '{subject}'.")


def _dispatch_user_email(task_name, *, user, purpose):
    from apps.core.tasks import enqueue_task

    try:
        enqueue_task(task_name, user_id=user.id)
        return True
    except Exception:
        logger.exception(
            "Failed to dispatch %s email",
            purpose,
            extra={"user_id": user.id, "email": user.email},
        )
        return False


def send_verification_email(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)
    verification_link = frontend_url("/verify-email", uid=uid, token=token)
    subject = f"{settings.EMAIL_SUBJECT_PREFIX}Verify your email"
    text_body = (
        f"Hi {user.first_name or user.email},\n\n"
        "Welcome. Please verify your email address to activate your account.\n\n"
        f"{verification_link}\n\n"
        "Once your email is verified, you can sign in normally without verifying again "
        "unless you change your email address."
    )
    html_body = (
        f"<p>Hi {user.first_name or user.email},</p>"
        "<p>Welcome. Please verify your email address to activate your account.</p>"
        f'<p><a href="{verification_link}">Verify your email</a></p>'
        "<p>Once your email is verified, you can sign in normally without verifying "
        "again unless you change your email address.</p>"
    )
    _send_email(
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        recipient_list=[user.email],
    )


def dispatch_verification_email(user):
    return _dispatch_user_email(
        "users.send_verification_email",
        user=user,
        purpose="verification",
    )


def send_password_reset_email(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = password_reset_token.make_token(user)
    reset_link = frontend_url("/reset-password", uid=uid, token=token)
    subject = f"{settings.EMAIL_SUBJECT_PREFIX}Password reset"
    text_body = (
        f"Hi {user.first_name or user.email},\n\n"
        "We received a request to reset your password.\n\n"
        f"{reset_link}\n\n"
        "If you did not request this, you can ignore this email."
    )
    html_body = (
        f"<p>Hi {user.first_name or user.email},</p>"
        "<p>We received a request to reset your password.</p>"
        f'<p><a href="{reset_link}">Reset your password</a></p>'
        "<p>If you did not request this, you can ignore this email.</p>"
    )
    _send_email(
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        recipient_list=[user.email],
    )


def dispatch_password_reset_email(user):
    return _dispatch_user_email(
        "users.send_password_reset_email",
        user=user,
        purpose="password reset",
    )
