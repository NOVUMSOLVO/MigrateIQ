from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.conf import settings
from django.db import connection
from django.core.cache import cache
from datetime import timedelta
import json
import psutil
import redis

from monitoring.models import SystemMetric, TenantMetric, PerformanceLog
from core.models import Tenant
from authentication.models import User


class Command(BaseCommand):
    help = 'Collect system and tenant metrics'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            dest='metric_type',
            default='all',
            choices=['all', 'system', 'tenant'],
            help='Type of metrics to collect (all, system, or tenant)',
        )
        parser.add_argument(
            '--tenant',
            dest='tenant_id',
            type=str,
            help='Collect metrics for specific tenant ID',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            dest='verbose',
            default=False,
            help='Enable verbose output',
        )
    
    def handle(self, *args, **options):
        metric_type = options['metric_type']
        tenant_id = options['tenant_id']
        verbose = options['verbose']
        
        if verbose:
            self.stdout.write(self.style.SUCCESS('Starting metrics collection...'))
        
        results = {
            'timestamp': timezone.now().isoformat(),
            'metrics_collected': 0,
            'errors': []
        }
        
        try:
            if metric_type in ['all', 'system']:
                system_count = self.collect_system_metrics(verbose)
                results['system_metrics'] = system_count
                results['metrics_collected'] += system_count
            
            if metric_type in ['all', 'tenant']:
                tenant_count = self.collect_tenant_metrics(tenant_id, verbose)
                results['tenant_metrics'] = tenant_count
                results['metrics_collected'] += tenant_count
            
            if verbose:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Metrics collection completed. Total metrics: {results['metrics_collected']}"
                    )
                )
            
            # Output summary
            self.stdout.write(json.dumps(results, indent=2))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during metrics collection: {e}"))
            raise CommandError(f"Metrics collection failed: {e}")
    
    def collect_system_metrics(self, verbose=False):
        """Collect system-wide metrics"""
        metrics_count = 0
        
        if verbose:
            self.stdout.write('Collecting system metrics...')
        
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_times = psutil.cpu_times()
            cpu_count = psutil.cpu_count()
            
            SystemMetric.objects.create(
                name='cpu_percent',
                value=cpu_percent,
                unit='%',
                category='cpu',
                metadata={
                    'cpu_count': cpu_count,
                    'cpu_times_user': cpu_times.user,
                    'cpu_times_system': cpu_times.system,
                    'cpu_times_idle': cpu_times.idle
                }
            )
            metrics_count += 1
            
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
            metrics_count += 1
            
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
            metrics_count += 1
            
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
            metrics_count += 1
            
            # Database metrics
            with connection.cursor() as cursor:
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
                    'db_name': db_name,
                    'db_size': db_size
                }
            )
            metrics_count += 1
            
            # Redis metrics (if configured)
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
                    metrics_count += 1
                except Exception as e:
                    if verbose:
                        self.stdout.write(self.style.WARNING(f"Redis metrics collection failed: {e}"))
            
            if verbose:
                self.stdout.write(f"Collected {metrics_count} system metrics")
        
        except Exception as e:
            if verbose:
                self.stdout.write(self.style.ERROR(f"Error collecting system metrics: {e}"))
            raise
        
        return metrics_count
    
    def collect_tenant_metrics(self, tenant_id=None, verbose=False):
        """Collect tenant-specific metrics"""
        metrics_count = 0
        
        if verbose:
            self.stdout.write('Collecting tenant metrics...')
        
        try:
            # Get tenants to process
            if tenant_id:
                tenants = Tenant.objects.filter(id=tenant_id)
                if not tenants.exists():
                    raise CommandError(f"Tenant with ID {tenant_id} not found")
            else:
                tenants = Tenant.objects.all()
            
            for tenant in tenants:
                if verbose:
                    self.stdout.write(f"Processing tenant: {tenant.name}")
                
                # User metrics
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
                metrics_count += 1
                
                if tenant.max_users > 0:
                    percent_used = (user_count / tenant.max_users) * 100
                    TenantMetric.objects.create(
                        tenant=tenant,
                        name='users_count_percent',
                        value=percent_used,
                        unit='%',
                        category='users'
                    )
                    metrics_count += 1
                
                # Storage metrics (placeholder - implement based on your data model)
                storage_used = 0  # Replace with actual calculation
                
                TenantMetric.objects.create(
                    tenant=tenant,
                    name='storage_used',
                    value=storage_used / (1024 * 1024),  # Convert to MB
                    unit='MB',
                    category='storage'
                )
                metrics_count += 1
                
                if tenant.max_storage_mb > 0:
                    percent_used = (storage_used / (tenant.max_storage_mb * 1024 * 1024)) * 100
                    TenantMetric.objects.create(
                        tenant=tenant,
                        name='storage_used_percent',
                        value=percent_used,
                        unit='%',
                        category='storage'
                    )
                    metrics_count += 1
                
                # API usage metrics
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
                metrics_count += 1
                
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
                    metrics_count += 1
                
                # Performance metrics
                from django.db.models import Avg, Max, Count, Q
                
                avg_performance = PerformanceLog.objects.filter(
                    tenant=tenant,
                    created_at__gte=timezone.now() - timedelta(days=7)
                ).aggregate(
                    avg_duration=Avg('duration_ms'),
                    max_duration=Max('duration_ms'),
                    total_operations=Count('id'),
                    error_count=Count('id', filter=Q(status='error'))
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
                    metrics_count += 1
            
            if verbose:
                self.stdout.write(f"Collected {metrics_count} tenant metrics")
        
        except Exception as e:
            if verbose:
                self.stdout.write(self.style.ERROR(f"Error collecting tenant metrics: {e}"))
            raise
        
        return metrics_count