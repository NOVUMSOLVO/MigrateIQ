from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import (
    Tenant, Domain, AuditLog, SystemConfiguration, Feature, TenantUsage,
    TenantQuota, TenantNotification
)


class DomainSerializer(serializers.ModelSerializer):
    """Serializer for Domain model."""

    class Meta:
        model = Domain
        fields = ['id', 'domain', 'is_primary', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class TenantSerializer(serializers.ModelSerializer):
    """Serializer for Tenant model."""

    domains = DomainSerializer(many=True, read_only=True)
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'description', 'contact_email',
            'contact_phone', 'subscription_plan', 'subscription_expires_at',
            'max_users', 'max_projects', 'max_data_sources', 'storage_limit_gb',
            'is_active', 'settings', 'domains', 'user_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user_count']

    def get_user_count(self, obj):
        """Get the number of users in this tenant."""
        return obj.users.count()

    def validate_slug(self, value):
        """Validate tenant slug uniqueness."""
        if self.instance:
            # Update case - exclude current instance
            if Tenant.objects.exclude(id=self.instance.id).filter(slug=value).exists():
                raise serializers.ValidationError(_('Tenant with this slug already exists.'))
        else:
            # Create case
            if Tenant.objects.filter(slug=value).exists():
                raise serializers.ValidationError(_('Tenant with this slug already exists.'))
        return value

    def validate_max_users(self, value):
        """Validate max users limit."""
        if value < 1:
            raise serializers.ValidationError(_('Max users must be at least 1.'))
        return value

    def validate_storage_limit_gb(self, value):
        """Validate storage limit."""
        if value < 0:
            raise serializers.ValidationError(_('Storage limit cannot be negative.'))
        return value


class TenantUsageSerializer(serializers.Serializer):
    """Serializer for tenant usage statistics."""

    user_count = serializers.IntegerField()
    max_users = serializers.IntegerField()
    project_count = serializers.IntegerField()
    max_projects = serializers.IntegerField()
    data_source_count = serializers.IntegerField()
    max_data_sources = serializers.IntegerField()
    storage_used_gb = serializers.FloatField()
    storage_limit_gb = serializers.FloatField()
    subscription_plan = serializers.CharField()
    subscription_expires_at = serializers.DateTimeField(allow_null=True)

    # Calculated fields
    user_usage_percentage = serializers.SerializerMethodField()
    project_usage_percentage = serializers.SerializerMethodField()
    data_source_usage_percentage = serializers.SerializerMethodField()
    storage_usage_percentage = serializers.SerializerMethodField()

    def get_user_usage_percentage(self, obj):
        """Calculate user usage percentage."""
        if obj['max_users'] == 0:
            return 0
        return round((obj['user_count'] / obj['max_users']) * 100, 2)

    def get_project_usage_percentage(self, obj):
        """Calculate project usage percentage."""
        if obj['max_projects'] == 0:
            return 0
        return round((obj['project_count'] / obj['max_projects']) * 100, 2)

    def get_data_source_usage_percentage(self, obj):
        """Calculate data source usage percentage."""
        if obj['max_data_sources'] == 0:
            return 0
        return round((obj['data_source_count'] / obj['max_data_sources']) * 100, 2)

    def get_storage_usage_percentage(self, obj):
        """Calculate storage usage percentage."""
        if obj['storage_limit_gb'] == 0:
            return 0
        return round((obj['storage_used_gb'] / obj['storage_limit_gb']) * 100, 2)


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog model."""

    user_name = serializers.SerializerMethodField()
    tenant_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'id', 'timestamp', 'user', 'user_name', 'tenant', 'tenant_name',
            'action', 'resource_type', 'resource_id', 'ip_address',
            'user_agent', 'metadata'
        ]
        read_only_fields = ['id', 'timestamp']

    def get_user_name(self, obj):
        """Get user's full name or username."""
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return None

    def get_tenant_name(self, obj):
        """Get tenant name."""
        if obj.tenant:
            return obj.tenant.name
        return None


class SystemConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for SystemConfiguration model."""

    class Meta:
        model = SystemConfiguration
        fields = [
            'id', 'key', 'value', 'description', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_key(self, value):
        """Validate configuration key uniqueness."""
        if self.instance:
            # Update case - exclude current instance
            if SystemConfiguration.objects.exclude(id=self.instance.id).filter(key=value).exists():
                raise serializers.ValidationError(_('Configuration with this key already exists.'))
        else:
            # Create case
            if SystemConfiguration.objects.filter(key=value).exists():
                raise serializers.ValidationError(_('Configuration with this key already exists.'))
        return value

    def validate_value(self, value):
        """Validate configuration value is not empty."""
        if not value.strip():
            raise serializers.ValidationError(_('Configuration value cannot be empty.'))
        return value


class FeatureSerializer(serializers.ModelSerializer):
    """Serializer for Feature model."""

    whitelisted_tenant_count = serializers.SerializerMethodField()

    class Meta:
        model = Feature
        fields = [
            'id', 'name', 'description', 'is_enabled', 'rollout_percentage',
            'whitelisted_tenants', 'whitelisted_tenant_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_whitelisted_tenant_count(self, obj):
        """Get count of whitelisted tenants."""
        return obj.whitelisted_tenants.count()

    def validate_name(self, value):
        """Validate feature name uniqueness."""
        if self.instance:
            # Update case - exclude current instance
            if Feature.objects.exclude(id=self.instance.id).filter(name=value).exists():
                raise serializers.ValidationError(_('Feature with this name already exists.'))
        else:
            # Create case
            if Feature.objects.filter(name=value).exists():
                raise serializers.ValidationError(_('Feature with this name already exists.'))
        return value

    def validate_rollout_percentage(self, value):
        """Validate rollout percentage is between 0 and 100."""
        if value < 0 or value > 100:
            raise serializers.ValidationError(_('Rollout percentage must be between 0 and 100.'))
        return value


class FeatureCheckSerializer(serializers.Serializer):
    """Serializer for feature check response."""

    enabled = serializers.BooleanField()
    feature_name = serializers.CharField(read_only=True)
    tenant_id = serializers.UUIDField(read_only=True, allow_null=True)
    rollout_percentage = serializers.IntegerField(read_only=True, allow_null=True)
    is_whitelisted = serializers.BooleanField(read_only=True, allow_null=True)


class TenantUsageSerializer(serializers.ModelSerializer):
    """Serializer for TenantUsage model."""

    tenant_name = serializers.ReadOnlyField(source='tenant.name')
    billing_period = serializers.SerializerMethodField()

    class Meta:
        model = TenantUsage
        fields = [
            'id', 'user_count', 'project_count', 'data_source_count',
            'storage_used_gb', 'api_calls_count', 'billing_period_start',
            'billing_period_end', 'base_cost', 'overage_cost', 'total_cost',
            'tenant_name', 'billing_period', 'created_at'
        ]
        read_only_fields = [
            'id', 'tenant_name', 'billing_period', 'created_at'
        ]

    def get_billing_period(self, obj):
        """Get formatted billing period."""
        return f"{obj.billing_period_start.strftime('%Y-%m')} to {obj.billing_period_end.strftime('%Y-%m')}"


class TenantQuotaSerializer(serializers.ModelSerializer):
    """Serializer for TenantQuota model."""

    tenant_name = serializers.ReadOnlyField(source='tenant.name')
    usage_percentages = serializers.SerializerMethodField()
    limit_warnings = serializers.SerializerMethodField()

    class Meta:
        model = TenantQuota
        fields = [
            'id', 'current_users', 'current_projects', 'current_data_sources',
            'current_storage_gb', 'api_calls_today', 'api_calls_this_hour',
            'last_api_call_reset', 'user_warning_threshold',
            'storage_warning_threshold', 'tenant_name', 'usage_percentages',
            'limit_warnings', 'updated_at'
        ]
        read_only_fields = [
            'id', 'current_users', 'current_projects', 'current_data_sources',
            'current_storage_gb', 'api_calls_today', 'api_calls_this_hour',
            'last_api_call_reset', 'tenant_name', 'usage_percentages',
            'limit_warnings', 'updated_at'
        ]

    def get_usage_percentages(self, obj):
        """Get usage percentages for all resources."""
        return {
            'users': obj.get_usage_percentage('users'),
            'projects': obj.get_usage_percentage('projects'),
            'storage': obj.get_usage_percentage('storage'),
        }

    def get_limit_warnings(self, obj):
        """Get limit warning status."""
        return {
            'user_limit_exceeded': obj.is_user_limit_exceeded(),
            'storage_limit_exceeded': obj.is_storage_limit_exceeded(),
            'api_limit_exceeded': obj.is_api_limit_exceeded(),
        }


class TenantNotificationSerializer(serializers.ModelSerializer):
    """Serializer for TenantNotification model."""

    tenant_name = serializers.ReadOnlyField(source='tenant.name')
    target_user_count = serializers.SerializerMethodField()
    is_visible_flag = serializers.SerializerMethodField()

    class Meta:
        model = TenantNotification
        fields = [
            'id', 'title', 'message', 'notification_type', 'target_users',
            'target_roles', 'is_active', 'is_dismissible', 'show_from',
            'show_until', 'tenant_name', 'target_user_count', 'is_visible_flag',
            'created_at'
        ]
        read_only_fields = [
            'id', 'tenant_name', 'target_user_count', 'is_visible_flag',
            'created_at'
        ]

    def get_target_user_count(self, obj):
        """Get count of targeted users."""
        return obj.target_users.count()

    def get_is_visible_flag(self, obj):
        """Check if notification is currently visible."""
        return obj.is_visible_now()


class TenantEnterpriseSerializer(serializers.ModelSerializer):
    """Enhanced serializer for Tenant model with enterprise features."""

    domain_count = serializers.SerializerMethodField()
    user_count = serializers.SerializerMethodField()
    quota_info = serializers.SerializerMethodField()
    feature_flags = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'description', 'is_active', 'plan',
            'max_users', 'max_projects', 'max_data_sources', 'max_storage_gb',
            'max_api_calls_per_hour', 'sso_enabled', 'sso_provider',
            'sso_config', 'gdpr_enabled', 'data_retention_days',
            'audit_log_retention_days', 'logo_url', 'primary_color',
            'secondary_color', 'settings', 'domain_count', 'user_count',
            'quota_info', 'feature_flags', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'slug', 'domain_count', 'user_count', 'quota_info',
            'feature_flags', 'created_at', 'updated_at'
        ]

    def get_domain_count(self, obj):
        """Get count of domains."""
        return obj.domains.count()

    def get_user_count(self, obj):
        """Get count of users."""
        return obj.users.count()

    def get_quota_info(self, obj):
        """Get quota information."""
        try:
            quota = obj.quota
            return {
                'current_users': quota.current_users,
                'current_projects': quota.current_projects,
                'current_storage_gb': quota.current_storage_gb,
                'usage_percentages': {
                    'users': quota.get_usage_percentage('users'),
                    'projects': quota.get_usage_percentage('projects'),
                    'storage': quota.get_usage_percentage('storage'),
                }
            }
        except TenantQuota.DoesNotExist:
            return None

    def get_feature_flags(self, obj):
        """Get enabled feature flags for tenant."""
        from .models import Feature
        features = Feature.objects.filter(is_enabled=True)
        enabled_features = []

        for feature in features:
            if feature.is_enabled_for_tenant(obj):
                enabled_features.append({
                    'name': feature.name,
                    'description': feature.description
                })

        return enabled_features