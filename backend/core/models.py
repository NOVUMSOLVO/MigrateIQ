from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
import uuid

User = get_user_model


class TimeStampedModel(models.Model):
    """Abstract base class with created_at and updated_at fields."""

    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)

    class Meta:
        abstract = True


class Tenant(TimeStampedModel):
    """Model representing a tenant in the multi-tenant system."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('Name'), max_length=100)
    slug = models.SlugField(_('Slug'), unique=True)
    description = models.TextField(_('Description'), blank=True)
    is_active = models.BooleanField(_('Is active'), default=True)

    # Subscription and billing
    plan = models.CharField(
        _('Plan'),
        max_length=20,
        choices=[
            ('free', _('Free')),
            ('basic', _('Basic')),
            ('professional', _('Professional')),
            ('enterprise', _('Enterprise')),
        ],
        default='free'
    )

    # Limits
    max_users = models.PositiveIntegerField(_('Max users'), default=5)
    max_projects = models.PositiveIntegerField(_('Max projects'), default=10)
    max_data_sources = models.PositiveIntegerField(_('Max data sources'), default=20)
    max_storage_gb = models.PositiveIntegerField(_('Max storage (GB)'), default=10)
    max_api_calls_per_hour = models.PositiveIntegerField(_('Max API calls per hour'), default=1000)

    # Enterprise features
    sso_enabled = models.BooleanField(_('SSO Enabled'), default=False)
    sso_provider = models.CharField(
        _('SSO Provider'),
        max_length=50,
        choices=[
            ('saml', _('SAML')),
            ('oauth2', _('OAuth2')),
            ('ldap', _('LDAP')),
        ],
        blank=True
    )
    sso_config = models.JSONField(_('SSO Configuration'), default=dict, blank=True)

    # Compliance settings
    gdpr_enabled = models.BooleanField(_('GDPR Enabled'), default=True)
    data_retention_days = models.PositiveIntegerField(_('Data Retention Days'), default=2555)  # 7 years
    audit_log_retention_days = models.PositiveIntegerField(_('Audit Log Retention Days'), default=2555)

    # Branding
    logo_url = models.URLField(_('Logo URL'), blank=True)
    primary_color = models.CharField(_('Primary Color'), max_length=7, blank=True)
    secondary_color = models.CharField(_('Secondary Color'), max_length=7, blank=True)

    # Settings
    settings = models.JSONField(_('Settings'), default=dict, blank=True)

    class Meta:
        verbose_name = _('Tenant')
        verbose_name_plural = _('Tenants')
        ordering = ['name']

    def __str__(self):
        return self.name


class Domain(TimeStampedModel):
    """Model representing a domain for tenant routing."""

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='domains',
        verbose_name=_('Tenant')
    )
    domain = models.CharField(_('Domain'), max_length=253, unique=True)
    is_primary = models.BooleanField(_('Is primary'), default=False)
    is_active = models.BooleanField(_('Is active'), default=True)

    class Meta:
        verbose_name = _('Domain')
        verbose_name_plural = _('Domains')
        unique_together = [['tenant', 'is_primary']]

    def __str__(self):
        return self.domain


class AuditLog(models.Model):
    """Model for audit logging."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        verbose_name=_('Tenant'),
        null=True,
        blank=True
    )
    user = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        related_name='audit_logs',
        verbose_name=_('User'),
        null=True,
        blank=True
    )

    # Action details
    action = models.CharField(_('Action'), max_length=100)
    resource_type = models.CharField(_('Resource type'), max_length=100)
    resource_id = models.CharField(_('Resource ID'), max_length=100, null=True, blank=True)

    # Request details
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    user_agent = models.TextField(_('User agent'), blank=True)

    # Additional data
    changes = models.JSONField(_('Changes'), default=dict, blank=True)
    metadata = models.JSONField(_('Metadata'), default=dict, blank=True)

    timestamp = models.DateTimeField(_('Timestamp'), auto_now_add=True)

    class Meta:
        verbose_name = _('Audit log')
        verbose_name_plural = _('Audit logs')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['tenant', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]

    def __str__(self):
        return f"{self.action} by {self.user} at {self.timestamp}"


class SystemConfiguration(TimeStampedModel):
    """Model for system-wide configuration."""

    key = models.CharField(_('Key'), max_length=100, unique=True)
    value = models.JSONField(_('Value'))
    description = models.TextField(_('Description'), blank=True)
    is_sensitive = models.BooleanField(_('Is sensitive'), default=False)
    is_active = models.BooleanField(_('Is active'), default=True)

    class Meta:
        verbose_name = _('System configuration')
        verbose_name_plural = _('System configurations')
        ordering = ['key']

    def __str__(self):
        return self.key


class Feature(TimeStampedModel):
    """Model for feature flags."""

    name = models.CharField(_('Name'), max_length=100, unique=True)
    description = models.TextField(_('Description'), blank=True)
    is_enabled = models.BooleanField(_('Is enabled'), default=False)

    # Targeting
    tenant_whitelist = models.ManyToManyField(
        Tenant,
        blank=True,
        related_name='whitelisted_features',
        verbose_name=_('Tenant whitelist')
    )

    # Rollout percentage (0-100)
    rollout_percentage = models.PositiveSmallIntegerField(
        _('Rollout percentage'),
        default=0,
        help_text=_('Percentage of users who should see this feature')
    )

    class Meta:
        verbose_name = _('Feature')
        verbose_name_plural = _('Features')
        ordering = ['name']

    def __str__(self):
        return self.name

    def is_enabled_for_tenant(self, tenant):
        """Check if feature is enabled for a specific tenant."""
        if not self.is_enabled:
            return False

        if self.tenant_whitelist.filter(id=tenant.id).exists():
            return True

        # Check rollout percentage
        import hashlib
        hash_input = f"{self.name}:{tenant.id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)
        return (hash_value % 100) < self.rollout_percentage


class TenantUsage(models.Model):
    """Model for tracking tenant resource usage."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='usage_records',
        verbose_name=_('Tenant')
    )

    # Usage metrics
    user_count = models.PositiveIntegerField(_('User Count'), default=0)
    project_count = models.PositiveIntegerField(_('Project Count'), default=0)
    data_source_count = models.PositiveIntegerField(_('Data Source Count'), default=0)
    storage_used_gb = models.FloatField(_('Storage Used (GB)'), default=0.0)
    api_calls_count = models.PositiveIntegerField(_('API Calls Count'), default=0)

    # Billing period
    billing_period_start = models.DateTimeField(_('Billing Period Start'))
    billing_period_end = models.DateTimeField(_('Billing Period End'))

    # Calculated costs
    base_cost = models.DecimalField(_('Base Cost'), max_digits=10, decimal_places=2, default=0)
    overage_cost = models.DecimalField(_('Overage Cost'), max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(_('Total Cost'), max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('Tenant Usage')
        verbose_name_plural = _('Tenant Usage Records')
        unique_together = [['tenant', 'billing_period_start']]
        ordering = ['-billing_period_start']

    def __str__(self):
        return f"{self.tenant.name} usage for {self.billing_period_start.strftime('%Y-%m')}"


class TenantQuota(models.Model):
    """Model for tenant resource quotas and limits."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.CASCADE,
        related_name='quota',
        verbose_name=_('Tenant')
    )

    # Current usage
    current_users = models.PositiveIntegerField(_('Current Users'), default=0)
    current_projects = models.PositiveIntegerField(_('Current Projects'), default=0)
    current_data_sources = models.PositiveIntegerField(_('Current Data Sources'), default=0)
    current_storage_gb = models.FloatField(_('Current Storage (GB)'), default=0.0)

    # API usage tracking
    api_calls_today = models.PositiveIntegerField(_('API Calls Today'), default=0)
    api_calls_this_hour = models.PositiveIntegerField(_('API Calls This Hour'), default=0)
    last_api_call_reset = models.DateTimeField(_('Last API Call Reset'), auto_now_add=True)

    # Soft limits (warnings)
    user_warning_threshold = models.FloatField(_('User Warning Threshold'), default=0.8)
    storage_warning_threshold = models.FloatField(_('Storage Warning Threshold'), default=0.8)

    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)

    class Meta:
        verbose_name = _('Tenant Quota')
        verbose_name_plural = _('Tenant Quotas')

    def __str__(self):
        return f"Quota for {self.tenant.name}"

    def is_user_limit_exceeded(self):
        """Check if user limit is exceeded."""
        return self.current_users >= self.tenant.max_users

    def is_storage_limit_exceeded(self):
        """Check if storage limit is exceeded."""
        return self.current_storage_gb >= self.tenant.max_storage_gb

    def is_api_limit_exceeded(self):
        """Check if API limit is exceeded."""
        return self.api_calls_this_hour >= self.tenant.max_api_calls_per_hour

    def get_usage_percentage(self, resource_type):
        """Get usage percentage for a resource type."""
        if resource_type == 'users':
            return (self.current_users / self.tenant.max_users) * 100 if self.tenant.max_users > 0 else 0
        elif resource_type == 'projects':
            return (self.current_projects / self.tenant.max_projects) * 100 if self.tenant.max_projects > 0 else 0
        elif resource_type == 'storage':
            return (self.current_storage_gb / self.tenant.max_storage_gb) * 100 if self.tenant.max_storage_gb > 0 else 0
        return 0


class TenantNotification(models.Model):
    """Model for tenant-specific notifications."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('Tenant')
    )

    title = models.CharField(_('Title'), max_length=200)
    message = models.TextField(_('Message'))

    notification_type = models.CharField(
        _('Type'),
        max_length=30,
        choices=[
            ('info', _('Information')),
            ('warning', _('Warning')),
            ('error', _('Error')),
            ('quota_warning', _('Quota Warning')),
            ('quota_exceeded', _('Quota Exceeded')),
            ('maintenance', _('Maintenance')),
            ('feature_update', _('Feature Update')),
        ]
    )

    # Targeting
    target_users = models.ManyToManyField(
        'authentication.User',
        blank=True,
        related_name='tenant_notifications',
        verbose_name=_('Target Users')
    )

    target_roles = models.JSONField(
        _('Target Roles'),
        default=list,
        blank=True,
        help_text=_('List of roles to target (empty means all users)')
    )

    # Status
    is_active = models.BooleanField(_('Is Active'), default=True)
    is_dismissible = models.BooleanField(_('Is Dismissible'), default=True)

    # Scheduling
    show_from = models.DateTimeField(_('Show From'), null=True, blank=True)
    show_until = models.DateTimeField(_('Show Until'), null=True, blank=True)

    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('Tenant Notification')
        verbose_name_plural = _('Tenant Notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['show_from', 'show_until']),
        ]

    def __str__(self):
        return f"{self.title} ({self.tenant.name})"

    def is_visible_now(self):
        """Check if notification should be visible now."""
        if not self.is_active:
            return False

        from django.utils import timezone
        now = timezone.now()

        if self.show_from and now < self.show_from:
            return False

        if self.show_until and now > self.show_until:
            return False

        return True