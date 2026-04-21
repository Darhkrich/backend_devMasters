from django.core.management.utils import get_random_secret_key

from .base import *  # noqa: F403


DEBUG = False
SECRET_KEY = SECRET_KEY or get_random_secret_key()  # noqa: F405
ALLOWED_HOSTS = ALLOWED_HOSTS or ["localhost", "127.0.0.1"]  # noqa: F405
CHANNEL_LAYERS = {  # noqa: F405
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}
CACHES = {  # noqa: F405
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "backend-dev-cache",
        "TIMEOUT": API_CACHE_TTL_SECONDS,  # noqa: F405
    }
}
TASK_QUEUE_MODE = "sync"

ROOT_URLCONF = 'config.urls'
