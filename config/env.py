import os
from typing import Iterable

from django.core.exceptions import ImproperlyConfigured


def env(name, default=None, *, required=False, cast=None):
    value = os.getenv(name, default)
    if required and (value is None or str(value).strip() == ""):
        raise ImproperlyConfigured(f"Missing required environment variable: {name}")
    if value is None:
        return value
    if cast:
        return cast(value)
    return value


def env_bool(name, default=False):
    return str(os.getenv(name, str(default))).strip().lower() in {"1", "true", "yes", "on"}


def env_int(name, default):
    return int(env(name, default=default))


def env_list(name, default=""):
    value = env(name, default=default)
    if not value:
        return []
    return [item.strip() for item in str(value).split(",") if item.strip()]


def validate_environment(app_env: str, *, debug: bool, required_vars: Iterable[str]):
    missing = [name for name in required_vars if not os.getenv(name)]
    if missing:
        raise ImproperlyConfigured(
            f"Missing required environment variables for {app_env}: {', '.join(missing)}"
        )

    if app_env in {"staging", "production"}:
        if debug:
            raise ImproperlyConfigured("DEBUG must be False outside development.")

        secret_key = os.getenv("SECRET_KEY", "")
        if not secret_key or secret_key.startswith("django-insecure-"):
            raise ImproperlyConfigured(
                "A strong SECRET_KEY must be configured for staging/production."
            )
