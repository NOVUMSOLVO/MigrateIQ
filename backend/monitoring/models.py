from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import TimeStampedModel, Tenant
from authentication.models import User


class SystemMetric(TimeStampedModel):
    """Model to store system-wide metrics for monitoring"""
    name = models.CharField(_('Metric Name'), max_length=100)
    value = models.FloatField(_('Metric Value'))
    unit = models.CharField(_('Unit'), max_length=50, blank=True)
    timestamp = models.DateTimeField(_('Timestamp'), auto_now_add=True)
    category = models.CharField(_('Category'), max_length=50, choices=[
        ('cpu', _('CPU')),
        ('memory', _('Memory')),
        ('disk', _('Disk')),
        ('network', _('Network')),
        ('database', _('Database')),
        ('application', _('Application')),
        ('other', _('Other')),
    ])
    
    class Meta:
        verbose_name = _('System Metric')
        verbose_name_plural = _('System Metrics')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.name}: {self.value} {self.unit} ({self.timestamp.strftime('%Y-%m-%d %H:%M:%S')})"


class TenantMetric(TimeStampedModel):
    """Model to store tenant-specific metrics"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='metrics')
    name = models.CharField(_('Metric Name'), max_length=100)
    value = models.FloatField(_('Metric Value'))
    unit = models.CharField(_('Unit'), max_length=50, blank=True)
    timestamp = models.DateTimeField(_('Timestamp'), auto_now_add=True)
    category = models.CharField(_('Category'), max_length=50, choices=[
        ('users', _('Users')),
        ('storage', _('Storage')),
        ('requests', _('API Requests')),
        ('performance', _('Performance')),
        ('migrations', _('Migrations')),
        ('other', _('Other')),
    ])
    
    class Meta:
        verbose_name = _('Tenant Metric')
        verbose_name_plural = _('Tenant Metrics')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['tenant']),
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.tenant.name} - {self.name}: {self.value} {self.unit}"


class PerformanceLog(TimeStampedModel):
    """Model to track performance of specific operations"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='performance_logs', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='performance_logs', null=True, blank=True)
    operation = models.CharField(_('Operation'), max_length=255)
    duration_ms = models.IntegerField(_('Duration (ms)'))
    status = models.CharField(_('Status'), max_length=50, choices=[
        ('success', _('Success')),
        ('error', _('Error')),
        ('timeout', _('Timeout')),
    ])
    resource_type = models.CharField(_('Resource Type'), max_length=100, blank=True)
    resource_id = models.CharField(_('Resource ID'), max_length=100, blank=True)
    metadata = models.JSONField(_('Metadata'), default=dict, blank=True)
    timestamp = models.DateTimeField(_('Timestamp'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Performance Log')
        verbose_name_plural = _('Performance Logs')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['tenant']),
            models.Index(fields=['operation']),
            models.Index(fields=['status']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.operation} - {self.duration_ms}ms ({self.status})"


class Alert(TimeStampedModel):
    """Model to store system and tenant alerts"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='alerts', null=True, blank=True)
    title = models.CharField(_('Title'), max_length=255)
    message = models.TextField(_('Message'))
    level = models.CharField(_('Level'), max_length=20, choices=[
        ('info', _('Information')),
        ('warning', _('Warning')),
        ('error', _('Error')),
        ('critical', _('Critical')),
    ])
    category = models.CharField(_('Category'), max_length=50, choices=[
        ('system', _('System')),
        ('security', _('Security')),
        ('performance', _('Performance')),
        ('usage', _('Usage')),
        ('other', _('Other')),
    ])
    is_active = models.BooleanField(_('Active'), default=True)
    resolved_at = models.DateTimeField(_('Resolved At'), null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='resolved_alerts', null=True, blank=True)
    resolution_notes = models.TextField(_('Resolution Notes'), blank=True)
    metadata = models.JSONField(_('Metadata'), default=dict, blank=True)
    
    class Meta:
        verbose_name = _('Alert')
        verbose_name_plural = _('Alerts')
        ordering = ['-created_at', '-level']
        indexes = [
            models.Index(fields=['tenant']),
            models.Index(fields=['level']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.get_level_display()}: {self.title}"
    
    def resolve(self, user=None, notes=''):
        """Mark the alert as resolved"""
        from django.utils import timezone
        self.is_active = False
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.resolution_notes = notes
        self.save()


class HealthCheckResult(TimeStampedModel):
    """Model to store results of system health checks"""
    check_name = models.CharField(_('Check Name'), max_length=100)
    status = models.CharField(_('Status'), max_length=20, choices=[
        ('ok', _('OK')),
        ('warning', _('Warning')),
        ('error', _('Error')),
    ])
    message = models.TextField(_('Message'), blank=True)
    details = models.JSONField(_('Details'), default=dict, blank=True)
    timestamp = models.DateTimeField(_('Timestamp'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Health Check Result')
        verbose_name_plural = _('Health Check Results')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['check_name']),
            models.Index(fields=['status']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.check_name}: {self.get_status_display()}"