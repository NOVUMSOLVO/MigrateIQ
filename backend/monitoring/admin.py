from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from .models import SystemMetric, TenantMetric, PerformanceLog, Alert, HealthCheckResult


@admin.register(SystemMetric)
class SystemMetricAdmin(admin.ModelAdmin):
    list_display = ('name', 'value_with_unit', 'category', 'created_at')
    list_filter = ('category', 'name', 'created_at')
    search_fields = ('name', 'category')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def value_with_unit(self, obj):
        return f"{obj.value} {obj.unit}"
    value_with_unit.short_description = _('Value')
    
    def has_change_permission(self, request, obj=None):
        # Metrics should be immutable once created
        return False


@admin.register(TenantMetric)
class TenantMetricAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant', 'value_with_unit', 'category', 'created_at')
    list_filter = ('category', 'name', 'tenant', 'created_at')
    search_fields = ('name', 'category', 'tenant__name')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def value_with_unit(self, obj):
        return f"{obj.value} {obj.unit}"
    value_with_unit.short_description = _('Value')
    
    def has_change_permission(self, request, obj=None):
        # Metrics should be immutable once created
        return False


@admin.register(PerformanceLog)
class PerformanceLogAdmin(admin.ModelAdmin):
    list_display = ('operation', 'resource_type', 'tenant', 'duration_ms', 'status', 'created_at')
    list_filter = ('status', 'operation', 'resource_type', 'tenant', 'created_at')
    search_fields = ('operation', 'resource_type', 'resource_id', 'tenant__name')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def has_change_permission(self, request, obj=None):
        # Performance logs should be immutable once created
        return False


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'level_colored', 'category', 'tenant', 'is_active', 'created_at', 'resolved_at')
    list_filter = ('level', 'category', 'is_active', 'tenant', 'created_at')
    search_fields = ('title', 'message', 'tenant__name')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    actions = ['mark_as_resolved']
    
    def level_colored(self, obj):
        colors = {
            'critical': 'darkred',
            'error': 'red',
            'warning': 'orange',
            'info': 'blue',
        }
        color = colors.get(obj.level, 'black')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.level.upper())
    level_colored.short_description = _('Level')
    
    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(is_active=False, resolved_at=timezone.now())
        self.message_user(request, _(f"{updated} alerts marked as resolved."))
    mark_as_resolved.short_description = _('Mark selected alerts as resolved')


@admin.register(HealthCheckResult)
class HealthCheckResultAdmin(admin.ModelAdmin):
    list_display = ('check_type', 'status_colored', 'message', 'created_at')
    list_filter = ('status', 'check_type', 'created_at')
    search_fields = ('check_type', 'message')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def status_colored(self, obj):
        colors = {
            'healthy': 'green',
            'warning': 'orange',
            'unhealthy': 'red',
            'skipped': 'gray',
        }
        color = colors.get(obj.status, 'black')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.status.upper())
    status_colored.short_description = _('Status')
    
    def has_change_permission(self, request, obj=None):
        # Health check results should be immutable once created
        return False


# Register custom admin site views
from django.contrib.admin.sites import AdminSite

class MonitoringAdminSite(AdminSite):
    site_header = _('MigrateIQ Monitoring')
    site_title = _('MigrateIQ Monitoring')
    index_title = _('Monitoring Dashboard')

# Uncomment to create a separate admin site for monitoring
# monitoring_admin_site = MonitoringAdminSite(name='monitoring_admin')
# monitoring_admin_site.register(SystemMetric, SystemMetricAdmin)
# monitoring_admin_site.register(TenantMetric, TenantMetricAdmin)
# monitoring_admin_site.register(PerformanceLog, PerformanceLogAdmin)
# monitoring_admin_site.register(Alert, AlertAdmin)
# monitoring_admin_site.register(HealthCheckResult, HealthCheckResultAdmin)