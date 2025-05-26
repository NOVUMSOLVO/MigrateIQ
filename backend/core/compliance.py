"""
Compliance and GDPR features for MigrateIQ.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
import uuid

User = get_user_model()


class DataRetentionPolicy(models.Model):
    """Model for data retention policies."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='retention_policies',
        verbose_name=_('Tenant')
    )
    
    name = models.CharField(_('Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    
    # Policy details
    data_type = models.CharField(
        _('Data Type'),
        max_length=50,
        choices=[
            ('user_data', _('User Data')),
            ('audit_logs', _('Audit Logs')),
            ('project_data', _('Project Data')),
            ('migration_data', _('Migration Data')),
            ('system_logs', _('System Logs')),
            ('backup_data', _('Backup Data')),
        ]
    )
    
    retention_period_days = models.PositiveIntegerField(
        _('Retention Period (Days)'),
        help_text=_('Number of days to retain data. 0 means indefinite retention.')
    )
    
    # Actions
    auto_delete = models.BooleanField(
        _('Auto Delete'),
        default=False,
        help_text=_('Automatically delete data after retention period.')
    )
    
    anonymize_before_delete = models.BooleanField(
        _('Anonymize Before Delete'),
        default=True,
        help_text=_('Anonymize data before deletion.')
    )
    
    # Status
    is_active = models.BooleanField(_('Is Active'), default=True)
    
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('Data Retention Policy')
        verbose_name_plural = _('Data Retention Policies')
        unique_together = [['tenant', 'data_type']]
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.tenant.name})"
    
    def get_deletion_date(self, created_date):
        """Calculate when data should be deleted."""
        if self.retention_period_days == 0:
            return None
        return created_date + timedelta(days=self.retention_period_days)


class DataProcessingRecord(models.Model):
    """Model for GDPR Article 30 - Records of Processing Activities."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='processing_records',
        verbose_name=_('Tenant')
    )
    
    # Processing details
    name = models.CharField(_('Processing Activity Name'), max_length=200)
    purpose = models.TextField(_('Purpose of Processing'))
    legal_basis = models.CharField(
        _('Legal Basis'),
        max_length=50,
        choices=[
            ('consent', _('Consent')),
            ('contract', _('Contract')),
            ('legal_obligation', _('Legal Obligation')),
            ('vital_interests', _('Vital Interests')),
            ('public_task', _('Public Task')),
            ('legitimate_interests', _('Legitimate Interests')),
        ]
    )
    
    # Data categories
    data_categories = models.JSONField(
        _('Data Categories'),
        default=list,
        help_text=_('List of personal data categories processed')
    )
    
    data_subjects = models.JSONField(
        _('Data Subjects'),
        default=list,
        help_text=_('Categories of data subjects')
    )
    
    # Recipients
    recipients = models.JSONField(
        _('Recipients'),
        default=list,
        help_text=_('Categories of recipients of personal data')
    )
    
    # International transfers
    third_country_transfers = models.BooleanField(
        _('Third Country Transfers'),
        default=False
    )
    transfer_safeguards = models.TextField(
        _('Transfer Safeguards'),
        blank=True,
        help_text=_('Safeguards for international transfers')
    )
    
    # Retention
    retention_period = models.CharField(
        _('Retention Period'),
        max_length=200,
        help_text=_('Time limits for erasure of data categories')
    )
    
    # Security measures
    security_measures = models.TextField(
        _('Security Measures'),
        help_text=_('Technical and organizational security measures')
    )
    
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('Data Processing Record')
        verbose_name_plural = _('Data Processing Records')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.tenant.name})"


class ConsentRecord(models.Model):
    """Model for tracking user consent."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='consent_records',
        verbose_name=_('User')
    )
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='consent_records',
        verbose_name=_('Tenant')
    )
    
    # Consent details
    purpose = models.CharField(
        _('Purpose'),
        max_length=100,
        choices=[
            ('data_processing', _('Data Processing')),
            ('marketing', _('Marketing')),
            ('analytics', _('Analytics')),
            ('third_party_sharing', _('Third Party Sharing')),
            ('cookies', _('Cookies')),
        ]
    )
    
    consent_given = models.BooleanField(_('Consent Given'))
    consent_text = models.TextField(_('Consent Text'))
    
    # Metadata
    ip_address = models.GenericIPAddressField(_('IP Address'), null=True, blank=True)
    user_agent = models.TextField(_('User Agent'), blank=True)
    
    # Timestamps
    given_at = models.DateTimeField(_('Given at'), auto_now_add=True)
    withdrawn_at = models.DateTimeField(_('Withdrawn at'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Consent Record')
        verbose_name_plural = _('Consent Records')
        unique_together = [['user', 'tenant', 'purpose']]
        ordering = ['-given_at']
    
    def __str__(self):
        status = 'Given' if self.consent_given else 'Withdrawn'
        return f"{self.user.email} - {self.purpose} ({status})"
    
    def withdraw_consent(self):
        """Withdraw consent."""
        self.consent_given = False
        self.withdrawn_at = timezone.now()
        self.save()


class DataSubjectRequest(models.Model):
    """Model for GDPR data subject requests."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='data_subject_requests',
        verbose_name=_('Tenant')
    )
    
    # Requester information
    requester_email = models.EmailField(_('Requester Email'))
    requester_name = models.CharField(_('Requester Name'), max_length=200, blank=True)
    
    # Request details
    request_type = models.CharField(
        _('Request Type'),
        max_length=30,
        choices=[
            ('access', _('Right of Access')),
            ('rectification', _('Right of Rectification')),
            ('erasure', _('Right of Erasure')),
            ('restrict_processing', _('Right to Restrict Processing')),
            ('data_portability', _('Right to Data Portability')),
            ('object', _('Right to Object')),
            ('withdraw_consent', _('Withdraw Consent')),
        ]
    )
    
    description = models.TextField(_('Description'))
    
    # Status
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=[
            ('pending', _('Pending')),
            ('in_progress', _('In Progress')),
            ('completed', _('Completed')),
            ('rejected', _('Rejected')),
        ],
        default='pending'
    )
    
    # Processing
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='assigned_data_requests',
        verbose_name=_('Assigned To'),
        null=True,
        blank=True
    )
    
    response = models.TextField(_('Response'), blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    due_date = models.DateTimeField(_('Due Date'))
    completed_at = models.DateTimeField(_('Completed at'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Data Subject Request')
        verbose_name_plural = _('Data Subject Requests')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['requester_email']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"{self.request_type} request from {self.requester_email}"
    
    def save(self, *args, **kwargs):
        """Set due date if not provided."""
        if not self.due_date:
            # GDPR requires response within 30 days
            self.due_date = timezone.now() + timedelta(days=30)
        super().save(*args, **kwargs)
    
    def is_overdue(self):
        """Check if request is overdue."""
        return timezone.now() > self.due_date and self.status != 'completed'


class ComplianceReport(models.Model):
    """Model for compliance reports."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='compliance_reports',
        verbose_name=_('Tenant')
    )
    
    name = models.CharField(_('Report Name'), max_length=200)
    report_type = models.CharField(
        _('Report Type'),
        max_length=30,
        choices=[
            ('gdpr_compliance', _('GDPR Compliance')),
            ('data_retention', _('Data Retention')),
            ('consent_overview', _('Consent Overview')),
            ('data_subject_requests', _('Data Subject Requests')),
            ('security_audit', _('Security Audit')),
        ]
    )
    
    # Report data
    report_data = models.JSONField(_('Report Data'), default=dict)
    
    # Generation details
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='generated_compliance_reports',
        verbose_name=_('Generated By'),
        null=True,
        blank=True
    )
    
    period_start = models.DateTimeField(_('Period Start'))
    period_end = models.DateTimeField(_('Period End'))
    
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Compliance Report')
        verbose_name_plural = _('Compliance Reports')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.tenant.name})"
