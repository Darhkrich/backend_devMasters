import os
from django.core.wsgi import get_wsgi_application
from config.settings_loader import resolve_settings_module

os.environ.setdefault('DJANGO_SETTINGS_MODULE', resolve_settings_module())
application = get_wsgi_application()
