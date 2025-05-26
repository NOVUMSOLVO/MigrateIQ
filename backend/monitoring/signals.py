from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from django.db import models
from core.models import Tenant
from authentication.models import User
from .models import Alert, SystemMetric, TenantMetric, PerformanceLog
import logging
import psutil

logger = logging.getLogger(__name__)


@receiver(post_save, sender=SystemMetric)
def check_system_metric_thresholds(sender, instance, created, **kwargs):
    """Check system metrics against thresholds and create alerts if needed"""
    if not created:
        return
    
    # Define thresholds for different metrics
    thresholds = {
        'cpu_percent': {'warning': 80, 'critical': 90},
        'memory_percent': {'warning': 80, 'critical': 90},
        'disk_percent': {'warning': 80, 'critical': 90},
    }
    
    # Check if this metric has thresholds defined
    if instance.name in thresholds:
        threshold = thresholds[instance.name]
        
        # Check against critical threshold
        if instance.value >= threshold['critical']:
            Alert.objects.create(
                title=_('Critical System Resource Usage'),
                message=_(f'{instance.name} is at {instance.value}{instance.unit}, which exceeds the critical threshold of {threshold["critical"]}{instance.unit}'),
                level='critical',
                category='system',
                metadata={
                    'metric_name': instance.name,
                    'metric_value': instance.value,
                    'metric_unit': instance.unit,
                    'threshold': threshold['critical']
                }
            )
        # Check against warning threshold
        elif instance.value >= threshold['warning']:
            Alert.objects.create(
                title=_('High System Resource Usage'),
                message=_(f'{instance.name} is at {instance.value}{instance.unit}, which exceeds the warning threshold of {threshold["warning"]}{instance.unit}'),
                level='warning',
                category='system',
                metadata={
                    'metric_name': instance.name,
                    'metric_value': instance.value,
                    'metric_unit': instance.unit,
                    'threshold': threshold['warning']
                }
            )


@receiver(post_save, sender=TenantMetric)
def check_tenant_metric_thresholds(sender, instance, created, **kwargs):
    """Check tenant metrics against thresholds and create alerts if needed"""
    if not created:
        return
    
    # Define thresholds for different metrics
    thresholds = {
        'storage_used_percent': {'warning': 80, 'critical': 90},
        'api_requests_rate': {'warning': 80, 'critical': 90},  # Percentage of limit
        'users_count_percent': {'warning': 80, 'critical': 90},  # Percentage of limit
    }
    
    # Check if this metric has thresholds defined
    if instance.name in thresholds:
        threshold = thresholds[instance.name]
        
        # Check against critical threshold
        if instance.value >= threshold['critical']:
            Alert.objects.create(
                tenant=instance.tenant,
                title=_('Critical Resource Usage'),
                message=_(f'{instance.name} is at {instance.value}{instance.unit}, which exceeds the critical threshold of {threshold["critical"]}{instance.unit}'),
                level='critical',
                category='usage',
                metadata={
                    'metric_name': instance.name,
                    'metric_value': instance.value,
                    'metric_unit': instance.unit,
                    'threshold': threshold['critical']
                }
            )
        # Check against warning threshold
        elif instance.value >= threshold['warning']:
            Alert.objects.create(
                tenant=instance.tenant,
                title=_('High Resource Usage'),
                message=_(f'{instance.name} is at {instance.value}{instance.unit}, which exceeds the warning threshold of {threshold["warning"]}{instance.unit}'),
                level='warning',
                category='usage',
                metadata={
                    'metric_name': instance.name,
                    'metric_value': instance.value,
                    'metric_unit': instance.unit,
                    'threshold': threshold['warning']
                }
            )


@receiver(post_save, sender=PerformanceLog)
def check_performance_issues(sender, instance, created, **kwargs):
    """Check performance logs for issues and create alerts if needed"""
    if not created:
        return
    
    # Define thresholds for different operations
    thresholds = {
        'default': 5000,  # 5 seconds in ms
        'data_migration': 60000,  # 1 minute in ms
        'data_transformation': 30000,  # 30 seconds in ms
        'data_validation': 20000,  # 20 seconds in ms
        'report_generation': 15000,  # 15 seconds in ms
    }
    
    # Get threshold for this operation or use default
    operation_threshold = thresholds.get(instance.operation, thresholds['default'])
    
    # Check if duration exceeds threshold
    if instance.duration_ms > operation_threshold:
        Alert.objects.create(
            tenant=instance.tenant,
            title=_('Performance Issue Detected'),
            message=_(f'Operation "{instance.operation}" took {instance.duration_ms}ms, which exceeds the threshold of {operation_threshold}ms'),
            level='warning',
            category='performance',
            metadata={
                'operation': instance.operation,
                'duration_ms': instance.duration_ms,
                'threshold_ms': operation_threshold,
                'resource_type': instance.resource_type,
                'resource_id': instance.resource_id
            }
        )
    
    # Check for errors
    if instance.status == 'error':
        Alert.objects.create(
            tenant=instance.tenant,
            title=_('Operation Error'),
            message=_(f'Operation "{instance.operation}" failed with an error'),
            level='error',
            category='performance',
            metadata={
                'operation': instance.operation,
                'duration_ms': instance.duration_ms,
                'resource_type': instance.resource_type,
                'resource_id': instance.resource_id,
                'error_details': instance.metadata.get('error', {})
            }
        )


@receiver(post_save, sender=Tenant)
def track_tenant_creation(sender, instance, created, **kwargs):
    """Track tenant creation and update events"""
    if created:
        # Log tenant creation
        Alert.objects.create(
            tenant=instance,
            title=_('New Tenant Created'),
            message=_(f'Tenant "{instance.name}" has been created'),
            level='info',
            category='system',
            metadata={
                'tenant_id': str(instance.id),
                'tenant_name': instance.name,
                'tenant_slug': instance.slug,
                'subscription_plan': instance.subscription_plan
            }
        )
        
        # Initialize tenant metrics
        TenantMetric.objects.create(
            tenant=instance,
            name='users_count',
            value=0,
            unit='users',
            category='users'
        )
        
        TenantMetric.objects.create(
            tenant=instance,
            name='storage_used',
            value=0,
            unit='MB',
            category='storage'
        )
        
        TenantMetric.objects.create(
            tenant=instance,
            name='api_requests_count',
            value=0,
            unit='requests',
            category='requests'
        )


@receiver(post_save, sender=User)
def track_user_creation(sender, instance, created, **kwargs):
    """Track user creation and update tenant metrics"""
    if created and instance.tenant:
        # Update tenant user count metric
        tenant_users = User.objects.filter(tenant=instance.tenant).count()
        
        TenantMetric.objects.create(
            tenant=instance.tenant,
            name='users_count',
            value=tenant_users,
            unit='users',
            category='users'
        )
        
        # Calculate percentage of user limit
        if instance.tenant.max_users > 0:
            percent_used = (tenant_users / instance.tenant.max_users) * 100
            
            TenantMetric.objects.create(
                tenant=instance.tenant,
                name='users_count_percent',
                value=percent_used,
                unit='%',
                category='users'
            )
            
            # Check if approaching user limit
            if percent_used >= 90:
                Alert.objects.create(
                    tenant=instance.tenant,
                    title=_('User Limit Nearly Reached'),
                    message=_(f'Tenant is using {tenant_users} of {instance.tenant.max_users} available user licenses ({percent_used:.1f}%)'),
                    level='warning',
                    category='usage',
                    metadata={
                        'current_users': tenant_users,
                        'max_users': instance.tenant.max_users,
                        'percent_used': percent_used
                    }
                )


# Schedule periodic system checks
def schedule_system_checks():
    """Schedule periodic system health checks"""
    from django.core.cache import cache
    from datetime import timedelta
    
    # Check if we've run recently (avoid duplicate runs in multi-process environments)
    last_run = cache.get('system_checks_last_run')
    now = timezone.now()
    
    if last_run and (now - last_run) < timedelta(minutes=5):
        return
    
    # Update last run time
    cache.set('system_checks_last_run', now, 300)  # 5 minutes
    
    try:
        # Check system resources
        cpu_percent = psutil.cpu_percent(interval=1)
        SystemMetric.objects.create(
            name='cpu_percent',
            value=cpu_percent,
            unit='%',
            category='cpu'
        )
        
        memory = psutil.virtual_memory()
        SystemMetric.objects.create(
            name='memory_percent',
            value=memory.percent,
            unit='%',
            category='memory'
        )
        
        disk = psutil.disk_usage('/')
        SystemMetric.objects.create(
            name='disk_percent',
            value=disk.percent,
            unit='%',
            category='disk'
        )
        
        # Check for long-running alerts
        old_alerts = Alert.objects.filter(
            is_active=True,
            created_at__lt=now - timedelta(days=7)
        )
        
        if old_alerts.exists():
            # Create a reminder alert
            Alert.objects.create(
                title=_('Unresolved Alerts Reminder'),
                message=_(f'There are {old_alerts.count()} alerts that have been active for more than 7 days'),
                level='warning',
                category='system',
                metadata={
                    'unresolved_count': old_alerts.count(),
                    'oldest_alert_id': str(old_alerts.order_by('created_at').first().id),
                    'oldest_alert_age_days': (now - old_alerts.order_by('created_at').first().created_at).days
                }
            )
    
    except Exception as e:
        logger.error(f"Error in scheduled system checks: {e}")


# Connect to app ready signal to schedule periodic tasks
from django.apps import apps
from django.db.models.signals import post_migrate

@receiver(post_migrate)
def setup_periodic_tasks(sender, **kwargs):
    """Set up periodic tasks after migrations"""
    if sender.name == 'monitoring':
        try:
            # Schedule periodic system checks using Celery if available
            if apps.is_installed('django_celery_beat'):
                from django_celery_beat.models import PeriodicTask, IntervalSchedule
                
                # Create or get interval schedule (every 5 minutes)
                schedule, _ = IntervalSchedule.objects.get_or_create(
                    every=5,
                    period=IntervalSchedule.MINUTES,
                )
                
                # Create or update the periodic task
                PeriodicTask.objects.update_or_create(
                    name='System health checks',
                    defaults={
                        'task': 'monitoring.tasks.run_system_checks',
                        'interval': schedule,
                        'enabled': True,
                    }
                )
                
                logger.info("Scheduled periodic system health checks")
        except Exception as e:
            logger.error(f"Error setting up periodic tasks: {e}")