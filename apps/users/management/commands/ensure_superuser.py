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
            user, created = User.objects.get_or_create(email=email)
            if created:
                user.set_password(password)
                user.is_superuser = True
                user.is_staff = True
                user.is_active = True
                user.email_verified = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Superuser {email} created.'))
            else:
                # Ensure existing user is superuser and staff
                if not user.is_superuser or not user.is_staff:
                    user.is_superuser = True
                    user.is_staff = True
                    user.save()
                    self.stdout.write(f'Superuser {email} upgraded to staff/superuser.')
                else:
                    self.stdout.write(f'Superuser {email} already exists.')
        else:
            self.stdout.write(self.style.WARNING('Superuser creation skipped: missing environment variables.'))