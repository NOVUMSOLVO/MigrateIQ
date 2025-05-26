from django.apps import AppConfig


class IntegrationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'integrations'
    verbose_name = 'Cloud Integrations'

    def ready(self):
        """Initialize cloud integrations when app is ready."""
        import integrations.signals  # noqa
