from config.env import validate_environment

from .staging import *  # noqa: F403


validate_environment(
    "production",
    debug=DEBUG,  # noqa: F405
    required_vars=["SECRET_KEY", "DB_PASSWORD", "AUDIT_LOG_SIGNING_KEY", "REDIS_URL"],
)

ROOT_URLCONF = 'config.urls'