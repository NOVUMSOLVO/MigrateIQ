from django.apps import AppConfig


class MonitoringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monitoring'
    verbose_name = 'System Monitoring'

    def ready(self):
        # Import signals to register them
        import monitoring.signals  # noqa