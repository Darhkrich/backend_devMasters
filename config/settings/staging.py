from config.env import validate_environment

from .base import *  # noqa: F403


DEBUG = True
validate_environment(
    "staging",
    debug=DEBUG,
    required_vars=["SECRET_KEY", "DB_PASSWORD", "AUDIT_LOG_SIGNING_KEY", "REDIS_URL"],
)

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", default=True)  # noqa: F405
SECURE_HSTS_SECONDS = env_int("SECURE_HSTS_SECONDS", 31536000)  # noqa: F405
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],  # noqa: F405
        },
    }
}
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_CACHE_URL or REDIS_URL,  # noqa: F405
        "TIMEOUT": API_CACHE_TTL_SECONDS,  # noqa: F405
    }
}
TASK_QUEUE_MODE = env("TASK_QUEUE_MODE", default="worker")  # noqa: F405


