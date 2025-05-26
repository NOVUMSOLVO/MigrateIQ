from celery import shared_task
from django.utils import timezone
from django.conf import settings
from django.db import connection
from django.core.cache import cache
from django.db.models import Avg, Max, Min, Count, Sum
from datetime import timedelta
import logging
import psutil
import redis
import json
import os

from .models import SystemMetric, TenantMetric, PerformanceLog, Alert, HealthCheckResult
from core.models import Tenant

logger = logging.getLogger(__name__)


@shared_task
def run_system_checks():
    """Run comprehensive system health checks"""
    from .signals import schedule_system_checks
    schedule_system_checks()
    return "System checks completed"


@shared_task
def collect_system_metrics():
    """Collect detailed system metrics"""
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_times = psutil.cpu_times()
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        SystemMetric.objects.create(
            name='cpu_percent',
            value=cpu_percent,
            unit='%',
            category='cpu',
            metadata={
                'cpu_count': cpu_count,
                'cpu_freq_current': cpu_freq.current if cpu_freq else None,
                'cpu_freq_max': cpu_freq.max if cpu_freq else None,
                'cpu_times_user': cpu_times.user,
                'cpu_times_system': cpu_times.system,
                'cpu_times_idle': cpu_times.idle
            }
        )
        
        # Memory metrics
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        SystemMetric.objects.create(
            name='memory_percent',
            value=memory.percent,
            unit='%',
            category='memory',
            metadata={
                'total_mb': memory.total / (1024 * 1024),
                'available_mb': memory.available / (1024 * 1024),
                'used_mb': memory.used / (1024 * 1024),
                'swap_percent': swap.percent,
                'swap_total_mb': swap.total / (1024 * 1024),
                'swap_used_mb': swap.used / (1024 * 1024)
            }
        )
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        
        SystemMetric.objects.create(
            name='disk_percent',
            value=disk.percent,
            unit='%',
            category='disk',
            metadata={
                'total_gb': disk.total / (1024 * 1024 * 1024),
                'used_gb': disk.used / (1024 * 1024 * 1024),
                'free_gb': disk.free / (1024 * 1024 * 1024),
                'read_count': disk_io.read_count if disk_io else None,
                'write_count': disk_io.write_count if disk_io else None,
                'read_bytes': disk_io.read_bytes if disk_io else None,
                'write_bytes': disk_io.write_bytes if disk_io else None
            }
        )
        
        # Network metrics
        net_io = psutil.net_io_counters()
        
        SystemMetric.objects.create(
            name='network_io',
            value=net_io.bytes_sent + net_io.bytes_recv,
            unit='bytes',
            category='network',
            metadata={
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'errin': net_io.errin,
                'errout': net_io.errout,
                'dropin': net_io.dropin,
                'dropout': net_io.dropout
            }
        )
        
        # Database metrics
        with connection.cursor() as cursor:
            # Get PostgreSQL stats
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()[0]
            
            cursor.execute("SELECT count(*) FROM pg_stat_activity;")
            active_connections = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT datname, pg_size_pretty(pg_database_size(datname)) as size 
                FROM pg_database 
                WHERE datname = current_database();
            """)
            db_size_result = cursor.fetchone()
            db_name, db_size = db_size_result if db_size_result else (None, None)
        
        SystemMetric.objects.create(
            name='database_connections',
            value=active_connections,
            unit='connections',
            category='database',
            metadata={
                'db_version': db_version,
                'db_name': db_name,
                'db_size': db_size
            }
        )
        
        # Redis metrics (if used)
        if hasattr(settings, 'CACHES') and settings.CACHES.get('default', {}).get('BACKEND') == 'django_redis.cache.RedisCache':
            try:
                redis_url = settings.CACHES['default']['LOCATION']
                redis_client = redis.from_url(redis_url)
                redis_info = redis_client.info()
                
                SystemMetric.objects.create(
                    name='redis_memory',
                    value=redis_info['used_memory'],
                    unit='bytes',
                    category='redis',
                    metadata={
                        'used_memory_peak': redis_info['used_memory_peak'],
                        'connected_clients': redis_info['connected_clients'],
                        'uptime_in_seconds': redis_info['uptime_in_seconds'],
                        'total_commands_processed': redis_info['total_commands_processed'],
                        'keyspace_hits': redis_info.get('keyspace_hits', 0),
                        'keyspace_misses': redis_info.get('keyspace_misses', 0)
                    }
                )
            except Exception as e:
                logger.error(f"Error collecting Redis metrics: {e}")
        
        # Application metrics
        SystemMetric.objects.create(
            name='application_uptime',
            value=(timezone.now() - timezone.datetime.fromtimestamp(
                os.path.getmtime(os.path.join(settings.BASE_DIR, 'manage.py')),
                tz=timezone.get_current_timezone()
            )).total_seconds(),
            unit='seconds',
            category='application'
        )
        
        return "System metrics collected successfully"
    
    except Exception as e:
        logger.error(f"Error collecting system metrics: {e}")
        return f"Error collecting system metrics: {str(e)}"


@shared_task
def collect_tenant_metrics():
    """Collect metrics for all tenants"""
    try:
        tenants = Tenant.objects.all()
        
        for tenant in tenants:
            # User metrics
            from authentication.models import User
            user_count = User.objects.filter(tenant=tenant).count()
            active_users_30d = User.objects.filter(
                tenant=tenant,
                last_login__gte=timezone.now() - timedelta(days=30)
            ).count()
            
            TenantMetric.objects.create(
                tenant=tenant,
                name='users_count',
                value=user_count,
                unit='users',
                category='users',
                metadata={
                    'active_users_30d': active_users_30d,
                    'active_percent': (active_users_30d / user_count * 100) if user_count > 0 else 0
                }
            )
            
            if tenant.max_users > 0:
                percent_used = (user_count / tenant.max_users) * 100
                TenantMetric.objects.create(
                    tenant=tenant,
                    name='users_count_percent',
                    value=percent_used,
                    unit='%',
                    category='users'
                )
            
            # Storage metrics
            # This is a placeholder - implement actual storage calculation based on your data model
            from django.db.models import Sum, F
            
            # Example: If you have a model with file size information
            # storage_used = tenant.files.aggregate(total=Sum('file_size'))['total'] or 0
            storage_used = 0  # Replace with actual calculation
            
            TenantMetric.objects.create(
                tenant=tenant,
                name='storage_used',
                value=storage_used / (1024 * 1024),  # Convert to MB
                unit='MB',
                category='storage'
            )
            
            if tenant.max_storage_mb > 0:
                percent_used = (storage_used / (tenant.max_storage_mb * 1024 * 1024)) * 100
                TenantMetric.objects.create(
                    tenant=tenant,
                    name='storage_used_percent',
                    value=percent_used,
                    unit='%',
                    category='storage'
                )
            
            # API usage metrics
            # This would typically come from your API request logging
            # For now, we'll use a placeholder
            from django.core.cache import cache
            api_requests_key = f"tenant:{tenant.id}:api_requests:30d"
            api_requests_30d = cache.get(api_requests_key, 0)
            
            TenantMetric.objects.create(
                tenant=tenant,
                name='api_requests_count',
                value=api_requests_30d,
                unit='requests',
                category='requests',
                metadata={
                    'daily_average': api_requests_30d / 30 if api_requests_30d > 0 else 0
                }
            )
            
            if tenant.max_api_requests_per_day > 0:
                daily_avg = api_requests_30d / 30 if api_requests_30d > 0 else 0
                percent_used = (daily_avg / tenant.max_api_requests_per_day) * 100
                TenantMetric.objects.create(
                    tenant=tenant,
                    name='api_requests_rate',
                    value=percent_used,
                    unit='%',
                    category='requests'
                )
            
            # Performance metrics
            avg_performance = PerformanceLog.objects.filter(
                tenant=tenant,
                created_at__gte=timezone.now() - timedelta(days=7)
            ).aggregate(
                avg_duration=Avg('duration_ms'),
                max_duration=Max('duration_ms'),
                total_operations=Count('id'),
                error_count=Count('id', filter=models.Q(status='error'))
            )
            
            if avg_performance['total_operations'] > 0:
                TenantMetric.objects.create(
                    tenant=tenant,
                    name='avg_operation_time',
                    value=avg_performance['avg_duration'] or 0,
                    unit='ms',
                    category='performance',
                    metadata={
                        'max_duration': avg_performance['max_duration'],
                        'total_operations': avg_performance['total_operations'],
                        'error_rate': (avg_performance['error_count'] / avg_performance['total_operations']) * 100
                    }
                )
        
        return "Tenant metrics collected successfully"
    
    except Exception as e:
        logger.error(f"Error collecting tenant metrics: {e}")
        return f"Error collecting tenant metrics: {str(e)}"


@shared_task
def run_health_checks():
    """Run comprehensive health checks and store results"""
    try:
        # Check database connection
        db_status = 'healthy'
        db_message = 'Database connection successful'
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception as e:
            db_status = 'unhealthy'
            db_message = f"Database connection failed: {str(e)}"
        
        HealthCheckResult.objects.create(
            check_type='database',
            status=db_status,
            message=db_message,
            metadata={}
        )
        
        # Check Redis connection
        redis_status = 'healthy'
        redis_message = 'Redis connection successful'
        try:
            if hasattr(settings, 'CACHES') and settings.CACHES.get('default', {}).get('BACKEND') == 'django_redis.cache.RedisCache':
                redis_url = settings.CACHES['default']['LOCATION']
                redis_client = redis.from_url(redis_url)
                redis_client.ping()
            else:
                redis_status = 'skipped'
                redis_message = 'Redis not configured'
        except Exception as e:
            redis_status = 'unhealthy'
            redis_message = f"Redis connection failed: {str(e)}"
        
        HealthCheckResult.objects.create(
            check_type='redis',
            status=redis_status,
            message=redis_message,
            metadata={}
        )
        
        # Check disk space
        disk = psutil.disk_usage('/')
        disk_status = 'healthy'
        disk_message = 'Sufficient disk space available'
        
        if disk.percent > 90:
            disk_status = 'unhealthy'
            disk_message = f"Disk usage critical: {disk.percent}%"
        elif disk.percent > 80:
            disk_status = 'warning'
            disk_message = f"Disk usage high: {disk.percent}%"
        
        HealthCheckResult.objects.create(
            check_type='disk',
            status=disk_status,
            message=disk_message,
            metadata={
                'total_gb': disk.total / (1024 * 1024 * 1024),
                'used_gb': disk.used / (1024 * 1024 * 1024),
                'free_gb': disk.free / (1024 * 1024 * 1024),
                'percent': disk.percent
            }
        )
        
        # Check memory
        memory = psutil.virtual_memory()
        memory_status = 'healthy'
        memory_message = 'Sufficient memory available'
        
        if memory.percent > 90:
            memory_status = 'unhealthy'
            memory_message = f"Memory usage critical: {memory.percent}%"
        elif memory.percent > 80:
            memory_status = 'warning'
            memory_message = f"Memory usage high: {memory.percent}%"
        
        HealthCheckResult.objects.create(
            check_type='memory',
            status=memory_status,
            message=memory_message,
            metadata={
                'total_mb': memory.total / (1024 * 1024),
                'available_mb': memory.available / (1024 * 1024),
                'used_mb': memory.used / (1024 * 1024),
                'percent': memory.percent
            }
        )
        
        # Check CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_status = 'healthy'
        cpu_message = 'CPU load normal'
        
        if cpu_percent > 90:
            cpu_status = 'unhealthy'
            cpu_message = f"CPU usage critical: {cpu_percent}%"
        elif cpu_percent > 80:
            cpu_status = 'warning'
            cpu_message = f"CPU usage high: {cpu_percent}%"
        
        HealthCheckResult.objects.create(
            check_type='cpu',
            status=cpu_status,
            message=cpu_message,
            metadata={
                'percent': cpu_percent,
                'count': psutil.cpu_count()
            }
        )
        
        # Check Celery (if applicable)
        celery_status = 'skipped'
        celery_message = 'Celery check skipped'
        
        if 'django_celery_results' in settings.INSTALLED_APPS:
            try:
                from celery.task.control import inspect
                insp = inspect()
                active_tasks = insp.active()
                
                if active_tasks is None:
                    celery_status = 'unhealthy'
                    celery_message = 'Celery workers not responding'
                else:
                    celery_status = 'healthy'
                    celery_message = 'Celery workers responding'
            except Exception as e:
                celery_status = 'unhealthy'
                celery_message = f"Celery check failed: {str(e)}"
        
        HealthCheckResult.objects.create(
            check_type='celery',
            status=celery_status,
            message=celery_message,
            metadata={}
        )
        
        # Overall system health
        health_checks = HealthCheckResult.objects.filter(
            created_at__gte=timezone.now() - timedelta(minutes=5)
        )
        
        if health_checks.filter(status='unhealthy').exists():
            system_status = 'unhealthy'
        elif health_checks.filter(status='warning').exists():
            system_status = 'warning'
        else:
            system_status = 'healthy'
        
        HealthCheckResult.objects.create(
            check_type='system',
            status=system_status,
            message=f"Overall system health: {system_status}",
            metadata={
                'checks_performed': health_checks.count(),
                'unhealthy_count': health_checks.filter(status='unhealthy').count(),
                'warning_count': health_checks.filter(status='warning').count(),
                'healthy_count': health_checks.filter(status='healthy').count()
            }
        )
        
        return "Health checks completed successfully"
    
    except Exception as e:
        logger.error(f"Error running health checks: {e}")
        return f"Error running health checks: {str(e)}"


@shared_task
def cleanup_old_metrics():
    """Clean up old metrics data to prevent database bloat"""
    try:
        # Define retention periods
        retention_periods = {
            'system_metrics': {
                'default': 90,  # days
                'high_frequency': 30  # days for metrics collected frequently
            },
            'tenant_metrics': {
                'default': 365,  # days
                'high_frequency': 90  # days for metrics collected frequently
            },
            'performance_logs': 180,  # days
            'health_checks': 30,  # days
            'resolved_alerts': 180  # days
        }
        
        # Clean up system metrics
        high_freq_cutoff = timezone.now() - timedelta(days=retention_periods['system_metrics']['high_frequency'])
        default_cutoff = timezone.now() - timedelta(days=retention_periods['system_metrics']['default'])
        
        # High frequency metrics (collected more than once per hour)
        high_freq_deleted = SystemMetric.objects.filter(
            created_at__lt=high_freq_cutoff,
            category__in=['cpu', 'memory']
        ).delete()
        
        # Other metrics
        default_deleted = SystemMetric.objects.filter(
            created_at__lt=default_cutoff
        ).exclude(category__in=['cpu', 'memory']).delete()
        
        # Clean up tenant metrics
        high_freq_cutoff = timezone.now() - timedelta(days=retention_periods['tenant_metrics']['high_frequency'])
        default_cutoff = timezone.now() - timedelta(days=retention_periods['tenant_metrics']['default'])
        
        # High frequency tenant metrics
        tenant_high_freq_deleted = TenantMetric.objects.filter(
            created_at__lt=high_freq_cutoff,
            category__in=['requests', 'performance']
        ).delete()
        
        # Other tenant metrics
        tenant_default_deleted = TenantMetric.objects.filter(
            created_at__lt=default_cutoff
        ).exclude(category__in=['requests', 'performance']).delete()
        
        # Clean up performance logs
        perf_cutoff = timezone.now() - timedelta(days=retention_periods['performance_logs'])
        perf_deleted = PerformanceLog.objects.filter(created_at__lt=perf_cutoff).delete()
        
        # Clean up health check results
        health_cutoff = timezone.now() - timedelta(days=retention_periods['health_checks'])
        health_deleted = HealthCheckResult.objects.filter(created_at__lt=health_cutoff).delete()
        
        # Clean up resolved alerts
        alert_cutoff = timezone.now() - timedelta(days=retention_periods['resolved_alerts'])
        alert_deleted = Alert.objects.filter(
            is_active=False,
            resolved_at__lt=alert_cutoff
        ).delete()
        
        return {
            'system_metrics_deleted': high_freq_deleted[0] + default_deleted[0],
            'tenant_metrics_deleted': tenant_high_freq_deleted[0] + tenant_default_deleted[0],
            'performance_logs_deleted': perf_deleted[0],
            'health_checks_deleted': health_deleted[0],
            'alerts_deleted': alert_deleted[0]
        }
    
    except Exception as e:
        logger.error(f"Error cleaning up old metrics: {e}")
        return f"Error cleaning up old metrics: {str(e)}"


@shared_task
def generate_system_report():
    """Generate a comprehensive system report"""
    try:
        now = timezone.now()
        report_period_start = now - timedelta(days=7)
        
        report = {
            'generated_at': now.isoformat(),
            'period': {
                'start': report_period_start.isoformat(),
                'end': now.isoformat(),
            },
            'system_health': {},
            'resource_usage': {},
            'tenant_stats': {},
            'performance': {},
            'alerts': {}
        }
        
        # System health
        latest_health = HealthCheckResult.objects.filter(
            check_type='system',
            created_at__gte=report_period_start
        ).order_by('-created_at').first()
        
        if latest_health:
            report['system_health']['current_status'] = latest_health.status
            report['system_health']['message'] = latest_health.message
            report['system_health']['last_updated'] = latest_health.created_at.isoformat()
        
        # Get health check history
        health_history = HealthCheckResult.objects.filter(
            check_type='system',
            created_at__gte=report_period_start
        ).values('status').annotate(count=Count('id'))
        
        report['system_health']['history'] = {
            item['status']: item['count'] for item in health_history
        }
        
        # Resource usage
        for resource in ['cpu', 'memory', 'disk']:
            metrics = SystemMetric.objects.filter(
                category=resource,
                created_at__gte=report_period_start
            ).aggregate(
                avg=Avg('value'),
                max=Max('value'),
                min=Min('value')
            )
            
            report['resource_usage'][resource] = {
                'average': metrics['avg'],
                'maximum': metrics['max'],
                'minimum': metrics['min'],
                'unit': '%'
            }
        
        # Tenant statistics
        tenant_count = Tenant.objects.count()
        active_tenants = Tenant.objects.filter(
            users__last_login__gte=report_period_start
        ).distinct().count()
        
        report['tenant_stats']['total'] = tenant_count
        report['tenant_stats']['active'] = active_tenants
        report['tenant_stats']['inactive'] = tenant_count - active_tenants
        
        # Get top tenants by API usage
        top_api_tenants = TenantMetric.objects.filter(
            name='api_requests_count',
            created_at__gte=report_period_start
        ).order_by('-value')[:5].values('tenant__name', 'value')
        
        report['tenant_stats']['top_api_usage'] = [
            {'tenant': item['tenant__name'], 'requests': item['value']} 
            for item in top_api_tenants
        ]
        
        # Performance metrics
        perf_metrics = PerformanceLog.objects.filter(
            created_at__gte=report_period_start
        ).aggregate(
            avg_duration=Avg('duration_ms'),
            max_duration=Max('duration_ms'),
            total_operations=Count('id'),
            error_count=Count('id', filter=models.Q(status='error'))
        )
        
        report['performance']['average_duration_ms'] = perf_metrics['avg_duration']
        report['performance']['max_duration_ms'] = perf_metrics['max_duration']
        report['performance']['total_operations'] = perf_metrics['total_operations']
        report['performance']['error_rate'] = (
            (perf_metrics['error_count'] / perf_metrics['total_operations']) * 100
            if perf_metrics['total_operations'] > 0 else 0
        )
        
        # Get slowest operations
        slowest_ops = PerformanceLog.objects.filter(
            created_at__gte=report_period_start
        ).order_by('-duration_ms')[:5].values('operation', 'duration_ms', 'tenant__name')
        
        report['performance']['slowest_operations'] = [
            {
                'operation': item['operation'],
                'duration_ms': item['duration_ms'],
                'tenant': item['tenant__name']
            } for item in slowest_ops
        ]
        
        # Alert statistics
        alert_stats = Alert.objects.filter(
            created_at__gte=report_period_start
        ).values('level').annotate(count=Count('id'))
        
        report['alerts']['by_level'] = {
            item['level']: item['count'] for item in alert_stats
        }
        
        alert_category_stats = Alert.objects.filter(
            created_at__gte=report_period_start
        ).values('category').annotate(count=Count('id'))
        
        report['alerts']['by_category'] = {
            item['category']: item['count'] for item in alert_category_stats
        }
        
        # Active alerts
        active_alerts = Alert.objects.filter(
            is_active=True
        ).count()
        
        report['alerts']['active_count'] = active_alerts
        
        # Save report to cache
        cache.set('system_report_latest', json.dumps(report), 86400)  # 24 hours
        
        return "System report generated successfully"
    
    except Exception as e:
        logger.error(f"Error generating system report: {e}")
        return f"Error generating system report: {str(e)}"