import os


def default_settings_module():
    app_env = os.getenv("APP_ENV", "development").strip().lower()
    mapping = {
        "development": "config.settings.dev",
        "dev": "config.settings.dev",
        "test": "config.settings.test",
        "testing": "config.settings.test",
        "staging": "config.settings.staging",
        "production": "config.settings.prod",
        "prod": "config.settings.prod",
    }
    return mapping.get(app_env, "config.settings.dev")


def resolve_settings_module():
    return os.getenv("DJANGO_SETTINGS_MODULE") or default_settings_module()
