from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Ensures a superuser exists based on environment variables'

    def handle(self, *args, **options):
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        if email and password:
            if not User.objects.filter(email=email).exists():
                # Create a username from the email (or use a fixed prefix)
                username = email.split('@')[0]
                User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password,
                    email_verified=True,
                )
                self.stdout.write(self.style.SUCCESS(f'Superuser {email} created.'))
            else:
                self.stdout.write(f'Superuser {email} already exists.')
        else:
            self.stdout.write(self.style.WARNING('Superuser creation skipped: missing environment variables.'))