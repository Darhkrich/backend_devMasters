import uuid

from django.core.management.base import BaseCommand, CommandError

from apps.security.models import UserSession
from apps.security.utils import log_security_event
from apps.users.models import DeviceSession, User


class Command(BaseCommand):
    help = "Anonymize a user account for privacy/deletion workflows."

    def add_arguments(self, parser):
        parser.add_argument("--user-id", type=int)
        parser.add_argument("--email")

    def handle(self, *args, **options):
        user_id = options.get("user_id")
        email = options.get("email")
        if not user_id and not email:
            raise CommandError("Provide --user-id or --email.")

        queryset = User.objects.all()
        if user_id:
            queryset = queryset.filter(id=user_id)
        if email:
            queryset = queryset.filter(email=email.lower().strip())

        user = queryset.first()
        if not user:
            raise CommandError("User not found.")

        replacement = f"deleted-{uuid.uuid4().hex[:12]}"
        user.email = f"{replacement}@example.invalid"
        user.username = replacement
        user.first_name = ""
        user.last_name = ""
        user.email_verified = False
        user.two_factor_enabled = False
        user.two_factor_secret = None
        user.is_active = False
        user.is_deleted = True
        user.set_unusable_password()
        user.save()

        DeviceSession.objects.filter(user=user).update(
            is_active=False,
            revoked_reason="User anonymized",
        )
        UserSession.objects.filter(user=user).update(is_active=False)

        log_security_event(
            user=user,
            event_type="DATA_DELETION",
            metadata={"workflow": "anonymize_user"},
        )

        self.stdout.write(self.style.SUCCESS(f"Anonymized user {user.id}."))
