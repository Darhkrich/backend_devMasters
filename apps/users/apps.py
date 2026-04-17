from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"

    def ready(self):
        from . import event_handlers  # noqa: F401
        from . import tasks  # noqa: F401
