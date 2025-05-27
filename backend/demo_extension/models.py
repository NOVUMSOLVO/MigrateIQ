from django.db import models
from core.models import TimeStampedModel, Tenant

class CustomDataConnector(TimeStampedModel):
    """Demo: Custom data connector for external APIs."""

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    api_endpoint = models.URLField()
    api_key = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    # Custom configuration
    sync_frequency = models.CharField(
        max_length=20,
        choices=[
            ('HOURLY', 'Every Hour'),
            ('DAILY', 'Daily'),
            ('WEEKLY', 'Weekly'),
        ],
        default='DAILY'
    )

    last_sync = models.DateTimeField(null=True, blank=True)
    records_synced = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Custom Data Connector'
        verbose_name_plural = 'Custom Data Connectors'

    def __str__(self):
        return f"{self.name} ({self.api_endpoint})"

class SyncLog(TimeStampedModel):
    """Log of synchronization activities."""

    connector = models.ForeignKey(CustomDataConnector, on_delete=models.CASCADE, related_name='sync_logs')
    status = models.CharField(
        max_length=20,
        choices=[
            ('SUCCESS', 'Success'),
            ('FAILED', 'Failed'),
            ('PARTIAL', 'Partial Success'),
        ]
    )
    records_processed = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    duration_seconds = models.FloatField(default=0.0)

    class Meta:
        verbose_name = 'Sync Log'
        verbose_name_plural = 'Sync Logs'
        ordering = ['-created_at']
