import os
from django.core.wsgi import get_wsgi_application
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Temporary workaround for Render free tier: run migrations on startup
try:
    # Try to access a table that should exist after migrations
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM security_blockedip LIMIT 1")
except Exception:
    # Table missing → run migrations
    call_command('migrate', interactive=False)

application = get_wsgi_application()