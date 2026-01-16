from django.apps import AppConfig


class MatchAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.match_app'

    def ready(self):
        # Importar signals para que se registren
        import apps.match_app.signals  # noqa: F401
