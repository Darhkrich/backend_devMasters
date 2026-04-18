from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Ensures a superuser exists with correct flags'

    def handle(self, *args, **options):
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        if not email or not password:
            self.stdout.write(self.style.WARNING('Superuser creation skipped: missing environment variables.'))
            return

        user, created = User.objects.get_or_create(email=email)
        if created or not user.check_password(password):
            user.set_password(password)
        user.is_superuser = True
        user.is_staff = True      # Required for admin access
        user.is_active = True
        user.email_verified = True  # Required by your login logic
        user.save()
        self.stdout.write(self.style.SUCCESS(f'Superuser {email} ensured (created={created}).'))