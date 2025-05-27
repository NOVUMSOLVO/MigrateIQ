"""
Models for cloud integrations.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from core.models import Tenant
import json


class CloudProvider(models.Model):
    """Model representing a cloud provider configuration."""

    PROVIDER_CHOICES = [
        ('aws', 'Amazon Web Services'),
        ('azure', 'Microsoft Azure'),
        ('gcp', 'Google Cloud Platform'),
        ('oracle', 'Oracle Cloud'),
        ('ibm', 'IBM Cloud'),
    ]

    name = models.CharField(_('Name'), max_length=100)
    provider = models.CharField(_('Provider'), max_length=20, choices=PROVIDER_CHOICES)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='cloud_providers')

    # Configuration
    region = models.CharField(_('Region'), max_length=50, blank=True)
    endpoint_url = models.URLField(_('Endpoint URL'), blank=True)

    # Credentials (encrypted)
    access_key = models.CharField(_('Access Key'), max_length=255, blank=True)
    secret_key = models.CharField(_('Secret Key'), max_length=255, blank=True)

    # Additional configuration as JSON
    config = models.JSONField(_('Configuration'), default=dict, blank=True)

    # Status
    is_active = models.BooleanField(_('Is Active'), default=True)
    last_tested = models.DateTimeField(_('Last Tested'), null=True, blank=True)
    test_status = models.CharField(
        _('Test Status'),
        max_length=20,
        choices=[
            ('pending', _('Pending')),
            ('success', _('Success')),
            ('failed', _('Failed')),
        ],
        default='pending'
    )
    test_message = models.TextField(_('Test Message'), blank=True)

    # Metadata
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = _('Cloud Provider')
        verbose_name_plural = _('Cloud Providers')
        unique_together = ['tenant', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_provider_display()})"


class CloudDataSource(models.Model):
    """Model representing a cloud data source."""

    SOURCE_TYPES = [
        # AWS
        ('s3', 'Amazon S3'),
        ('rds', 'Amazon RDS'),
        ('redshift', 'Amazon Redshift'),
        ('dynamodb', 'Amazon DynamoDB'),
        ('athena', 'Amazon Athena'),

        # Azure
        ('blob_storage', 'Azure Blob Storage'),
        ('sql_database', 'Azure SQL Database'),
        ('synapse', 'Azure Synapse'),
        ('cosmos_db', 'Azure Cosmos DB'),
        ('data_lake', 'Azure Data Lake'),

        # GCP
        ('cloud_storage', 'Google Cloud Storage'),
        ('cloud_sql', 'Google Cloud SQL'),
        ('bigquery', 'Google BigQuery'),
        ('firestore', 'Google Firestore'),
        ('bigtable', 'Google Bigtable'),
    ]

    name = models.CharField(_('Name'), max_length=100)
    source_type = models.CharField(_('Source Type'), max_length=30, choices=SOURCE_TYPES)
    provider = models.ForeignKey(CloudProvider, on_delete=models.CASCADE, related_name='data_sources')

    # Connection details
    connection_string = models.TextField(_('Connection String'), blank=True)
    database_name = models.CharField(_('Database Name'), max_length=100, blank=True)
    schema_name = models.CharField(_('Schema Name'), max_length=100, blank=True)

    # Source-specific configuration
    bucket_name = models.CharField(_('Bucket/Container Name'), max_length=100, blank=True)
    table_name = models.CharField(_('Table Name'), max_length=100, blank=True)
    file_path = models.CharField(_('File Path'), max_length=500, blank=True)
    file_format = models.CharField(
        _('File Format'),
        max_length=20,
        choices=[
            ('csv', 'CSV'),
            ('json', 'JSON'),
            ('parquet', 'Parquet'),
            ('avro', 'Avro'),
            ('orc', 'ORC'),
            ('xml', 'XML'),
        ],
        blank=True
    )

    # Additional configuration
    config = models.JSONField(_('Configuration'), default=dict, blank=True)

    # Status
    is_active = models.BooleanField(_('Is Active'), default=True)
    last_synced = models.DateTimeField(_('Last Synced'), null=True, blank=True)
    sync_status = models.CharField(
        _('Sync Status'),
        max_length=20,
        choices=[
            ('pending', _('Pending')),
            ('syncing', _('Syncing')),
            ('success', _('Success')),
            ('failed', _('Failed')),
        ],
        default='pending'
    )

    # Metadata
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Cloud Data Source')
        verbose_name_plural = _('Cloud Data Sources')
        unique_together = ['provider', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"


class CloudMigrationJob(models.Model):
    """Model representing a cloud migration job."""

    JOB_TYPES = [
        ('import', _('Import from Cloud')),
        ('export', _('Export to Cloud')),
        ('sync', _('Synchronize')),
        ('backup', _('Backup')),
        ('restore', _('Restore')),
    ]

    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('running', _('Running')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
    ]

    name = models.CharField(_('Name'), max_length=100)
    job_type = models.CharField(_('Job Type'), max_length=20, choices=JOB_TYPES)
    source = models.ForeignKey(
        CloudDataSource,
        on_delete=models.CASCADE,
        related_name='migration_jobs_as_source',
        null=True,
        blank=True
    )
    target = models.ForeignKey(
        CloudDataSource,
        on_delete=models.CASCADE,
        related_name='migration_jobs_as_target',
        null=True,
        blank=True
    )

    # Job configuration
    config = models.JSONField(_('Configuration'), default=dict, blank=True)
    schedule = models.CharField(_('Schedule'), max_length=100, blank=True)  # Cron expression

    # Status and progress
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.PositiveIntegerField(_('Progress'), default=0)  # 0-100

    # Execution details
    started_at = models.DateTimeField(_('Started At'), null=True, blank=True)
    completed_at = models.DateTimeField(_('Completed At'), null=True, blank=True)
    error_message = models.TextField(_('Error Message'), blank=True)

    # Statistics
    records_processed = models.PositiveIntegerField(_('Records Processed'), default=0)
    records_failed = models.PositiveIntegerField(_('Records Failed'), default=0)
    bytes_transferred = models.BigIntegerField(_('Bytes Transferred'), default=0)

    # Metadata
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = _('Cloud Migration Job')
        verbose_name_plural = _('Cloud Migration Jobs')

    def __str__(self):
        return f"{self.name} ({self.get_job_type_display()})"


class CloudCredential(models.Model):
    """Model for storing encrypted cloud credentials."""

    name = models.CharField(_('Name'), max_length=100)
    provider = models.ForeignKey(CloudProvider, on_delete=models.CASCADE, related_name='credentials')

    # Credential types
    credential_type = models.CharField(
        _('Credential Type'),
        max_length=30,
        choices=[
            ('access_key', _('Access Key')),
            ('service_account', _('Service Account')),
            ('connection_string', _('Connection String')),
            ('oauth_token', _('OAuth Token')),
            ('certificate', _('Certificate')),
        ]
    )

    # Encrypted credential data
    encrypted_data = models.TextField(_('Encrypted Data'))

    # Metadata
    expires_at = models.DateTimeField(_('Expires At'), null=True, blank=True)
    is_active = models.BooleanField(_('Is Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Cloud Credential')
        verbose_name_plural = _('Cloud Credentials')
        unique_together = ['provider', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_credential_type_display()})"
