from django.apps import AppConfig

class MessagesAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.messages_app'

    def ready(self):
        import apps.messages_app.signals