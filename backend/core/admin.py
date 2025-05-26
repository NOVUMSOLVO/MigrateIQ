from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json
from .models import Tenant, Domain, AuditLog, SystemConfiguration, Feature


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """Admin configuration for Tenant model."""
    
    list_display = (
        'name', 'slug', 'subscription_plan', 'is_active', 
        'user_count', 'created_at'
    )
    list_filter = ('subscription_plan', 'is_active', 'created_at')
    search_fields = ('name', 'slug', 'contact_email')
    readonly_fields = ('id', 'created_at', 'updated_at', 'user_count')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description')
        }),
        (_('Contact Information'), {
            'fields': ('contact_email', 'contact_phone')
        }),
        (_('Subscription'), {
            'fields': ('subscription_plan', 'subscription_expires_at')
        }),
        (_('Limits'), {
            'fields': (
                'max_users', 'max_projects', 'max_data_sources',
                'storage_limit_gb'
            )
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
        (_('Settings'), {
            'fields': ('settings',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_count(self, obj):
        """Display user count for the tenant."""
        count = obj.users.count()
        url = reverse('admin:authentication_user_changelist') + f'?tenant__id__exact={obj.id}'
        return format_html('<a href="{}">{} users</a>', url, count)
    user_count.short_description = _('Users')
    
    def get_queryset(self, request):
        """Superusers see all tenants, others see only their tenant."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request, 'tenant') and request.tenant:
            return qs.filter(id=request.tenant.id)
        return qs.none()


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    """Admin configuration for Domain model."""
    
    list_display = ('domain', 'tenant', 'is_primary', 'is_active', 'created_at')
    list_filter = ('is_primary', 'is_active', 'created_at')
    search_fields = ('domain', 'tenant__name')
    readonly_fields = ('id', 'created_at')
    ordering = ('domain',)
    
    fieldsets = (
        (None, {
            'fields': ('domain', 'tenant')
        }),
        (_('Settings'), {
            'fields': ('is_primary', 'is_active')
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Filter domains by tenant for non-superusers."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request, 'tenant') and request.tenant:
            return qs.filter(tenant=request.tenant)
        return qs.none()


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin configuration for AuditLog model."""
    
    list_display = (
        'timestamp', 'user', 'action', 'resource_type', 
        'resource_id', 'ip_address', 'tenant'
    )
    list_filter = (
        'action', 'resource_type', 'tenant', 'timestamp'
    )
    search_fields = (
        'user__username', 'user__email', 'action', 
        'resource_type', 'resource_id', 'ip_address'
    )
    readonly_fields = (
        'id', 'timestamp', 'user', 'tenant', 'action',
        'resource_type', 'resource_id', 'ip_address',
        'user_agent', 'metadata_display'
    )
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        (None, {
            'fields': (
                'timestamp', 'user', 'tenant', 'action'
            )
        }),
        (_('Resource'), {
            'fields': ('resource_type', 'resource_id')
        }),
        (_('Request Info'), {
            'fields': ('ip_address', 'user_agent')
        }),
        (_('Metadata'), {
            'fields': ('metadata_display',),
            'classes': ('collapse',)
        }),
    )
    
    def metadata_display(self, obj):
        """Display formatted metadata."""
        if obj.metadata:
            formatted = json.dumps(obj.metadata, indent=2)
            return format_html('<pre>{}</pre>', formatted)
        return '-'
    metadata_display.short_description = _('Metadata')
    
    def get_queryset(self, request):
        """Filter audit logs by tenant for non-superusers."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request, 'tenant') and request.tenant:
            return qs.filter(tenant=request.tenant)
        return qs.none()
    
    def has_add_permission(self, request):
        """Disable manual audit log creation."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable audit log editing."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete audit logs."""
        return request.user.is_superuser


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    """Admin configuration for SystemConfiguration model."""
    
    list_display = ('key', 'description', 'is_active', 'updated_at')
    list_filter = ('is_active', 'updated_at')
    search_fields = ('key', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('key',)
    
    fieldsets = (
        (None, {
            'fields': ('key', 'value', 'description')
        }),
        (_('Settings'), {
            'fields': ('is_active',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Only superusers can manage system configurations."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.none()
    
    def has_module_permission(self, request):
        """Only superusers can access this module."""
        return request.user.is_superuser


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    """Admin configuration for Feature model."""
    
    list_display = (
        'name', 'is_enabled', 'rollout_percentage', 
        'whitelisted_tenants_count', 'updated_at'
    )
    list_filter = ('is_enabled', 'updated_at')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at', 'whitelisted_tenants_count')
    filter_horizontal = ('whitelisted_tenants',)
    ordering = ('name',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        (_('Rollout Settings'), {
            'fields': ('is_enabled', 'rollout_percentage')
        }),
        (_('Tenant Whitelist'), {
            'fields': ('whitelisted_tenants',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def whitelisted_tenants_count(self, obj):
        """Display count of whitelisted tenants."""
        count = obj.whitelisted_tenants.count()
        if count > 0:
            url = reverse('admin:core_tenant_changelist')
            return format_html(
                '<a href="{}?feature__id__exact={}">{} tenants</a>',
                url, obj.id, count
            )
        return '0 tenants'
    whitelisted_tenants_count.short_description = _('Whitelisted Tenants')
    
    def get_queryset(self, request):
        """Only superusers can manage feature flags."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.none()
    
    def has_module_permission(self, request):
        """Only superusers can access this module."""
        return request.user.is_superuser