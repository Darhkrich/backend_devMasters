from django.db import migrations
from django.contrib.auth import get_user_model
import os

def create_superuser(apps, schema_editor):
    User = get_user_model()
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
    if email and password:
        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(
                email=email,
                password=password,
                email_verified=True,      # Important: set email as verified
                is_active=True,
            )
            print(f"Superuser {email} created with email_verified=True.")
        else:
            print(f"Superuser {email} already exists.")
    else:
        print("Superuser creation skipped: missing environment variables.")

def reverse_func(apps, schema_editor):
    # Optional: delete the superuser if needed, but we skip for safety
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0016_user_bio_user_date_format_user_language_and_more.py'),   # ← Replace with the actual last migration file name
    ]
    operations = [
        migrations.RunPython(create_superuser, reverse_func),
    ]