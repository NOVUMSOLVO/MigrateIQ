import time
import json
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.conf import settings
from django.db import connection
from django.core.cache import cache
import psutil
import redis

from monitoring.models import HealthCheckResult, SystemMetric


class Command(BaseCommand):
    help = 'Run a comprehensive system health check and report results'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--save',
            action='store_true',
            dest='save',
            default=True,
            help='Save health check results to database',
        )
        parser.add_argument(
            '--format',
            dest='format',
            default='text',
            choices=['text', 'json'],
            help='Output format (text or json)',
        )
    
    def handle(self, *args, **options):
        save_results = options['save']
        output_format = options['format']
        
        self.stdout.write(self.style.SUCCESS('Starting system health check...'))
        
        # Run health checks
        results = self.run_health_checks()
        
        # Save results if requested
        if save_results:
            self.save_health_check_results(results)
        
        # Output results in requested format
        if output_format == 'json':
            self.stdout.write(json.dumps(results, indent=2))
        else:
            self.output_text_results(results)
    
    def run_health_checks(self):
        """Run comprehensive health checks"""
        results = {
            'timestamp': timezone.now().isoformat(),
            'checks': {}
        }
        
        # Check database
        db_result = self.check_database()
        results['checks']['database'] = db_result
        
        # Check Redis
        redis_result = self.check_redis()
        results['checks']['redis'] = redis_result
        
        # Check disk
        disk_result = self.check_disk()
        results['checks']['disk'] = disk_result
        
        # Check memory
        memory_result = self.check_memory()
        results['checks']['memory'] = memory_result
        
        # Check CPU
        cpu_result = self.check_cpu()
        results['checks']['cpu'] = cpu_result
        
        # Check Celery
        celery_result = self.check_celery()
        results['checks']['celery'] = celery_result
        
        # Determine overall status
        statuses = [check['status'] for check in results['checks'].values()]
        if 'unhealthy' in statuses:
            overall_status = 'unhealthy'
        elif 'warning' in statuses:
            overall_status = 'warning'
        else:
            overall_status = 'healthy'
        
        results['overall_status'] = overall_status
        
        return results
    
    def check_database(self):
        """Check database connection and health"""
        start_time = time.time()
        result = {
            'status': 'healthy',
            'message': 'Database connection successful',
            'metadata': {}
        }
        
        try:
            # Check connection
            with connection.cursor() as cursor:
                # Check if we can execute a simple query
                cursor.execute("SELECT 1")
                cursor.fetchone()
                
                # Get PostgreSQL version
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                result['metadata']['version'] = version
                
                # Get connection count
                cursor.execute("SELECT count(*) FROM pg_stat_activity")
                connections = cursor.fetchone()[0]
                result['metadata']['active_connections'] = connections
                
                # Check for long-running queries
                cursor.execute("""
                    SELECT count(*) FROM pg_stat_activity 
                    WHERE state = 'active' 
                    AND query_start < NOW() - INTERVAL '5 minutes'
                """)
                long_queries = cursor.fetchone()[0]
                result['metadata']['long_running_queries'] = long_queries
                
                if long_queries > 0:
                    result['status'] = 'warning'
                    result['message'] = f"Database has {long_queries} long-running queries"
        
        except Exception as e:
            result['status'] = 'unhealthy'
            result['message'] = f"Database connection failed: {str(e)}"
        
        # Calculate response time
        result['metadata']['response_time_ms'] = (time.time() - start_time) * 1000
        
        return result
    
    def check_redis(self):
        """Check Redis connection and health"""
        start_time = time.time()
        result = {
            'status': 'skipped',
            'message': 'Redis not configured',
            'metadata': {}
        }
        
        # Skip if Redis is not configured
        if not hasattr(settings, 'CACHES') or settings.CACHES.get('default', {}).get('BACKEND') != 'django_redis.cache.RedisCache':
            return result
        
        try:
            # Get Redis connection
            redis_url = settings.CACHES['default']['LOCATION']
            redis_client = redis.from_url(redis_url)
            
            # Check connection with ping
            ping_response = redis_client.ping()
            if not ping_response:
                raise Exception("Redis ping failed")
            
            # Get Redis info
            info = redis_client.info()
            
            result['status'] = 'healthy'
            result['message'] = 'Redis connection successful'
            result['metadata'] = {
                'version': info.get('redis_version'),
                'used_memory': info.get('used_memory_human'),
                'used_memory_peak': info.get('used_memory_peak_human'),
                'connected_clients': info.get('connected_clients'),
                'uptime_days': info.get('uptime_in_seconds') / 86400 if 'uptime_in_seconds' in info else 0,
            }
            
            # Check memory usage
            if 'used_memory' in info and 'maxmemory' in info and info['maxmemory'] > 0:
                memory_percent = (info['used_memory'] / info['maxmemory']) * 100
                result['metadata']['memory_percent'] = memory_percent
                
                if memory_percent > 90:
                    result['status'] = 'warning'
                    result['message'] = f"Redis memory usage is high: {memory_percent:.1f}%"
        
        except Exception as e:
            result['status'] = 'unhealthy'
            result['message'] = f"Redis connection failed: {str(e)}"
        
        # Calculate response time
        result['metadata']['response_time_ms'] = (time.time() - start_time) * 1000
        
        return result
    
    def check_disk(self):
        """Check disk space usage"""
        result = {
            'status': 'healthy',
            'message': 'Sufficient disk space available',
            'metadata': {}
        }
        
        try:
            # Get disk usage for root partition
            disk = psutil.disk_usage('/')
            
            # Convert to human-readable format
            total_gb = disk.total / (1024 * 1024 * 1024)
            used_gb = disk.used / (1024 * 1024 * 1024)
            free_gb = disk.free / (1024 * 1024 * 1024)
            
            result['metadata'] = {
                'total_gb': round(total_gb, 2),
                'used_gb': round(used_gb, 2),
                'free_gb': round(free_gb, 2),
                'percent': disk.percent
            }
            
            # Check thresholds
            if disk.percent > 90:
                result['status'] = 'unhealthy'
                result['message'] = f"Disk usage critical: {disk.percent}%"
            elif disk.percent > 80:
                result['status'] = 'warning'
                result['message'] = f"Disk usage high: {disk.percent}%"
            
            # Check for project directory
            if hasattr(settings, 'BASE_DIR'):
                project_disk = psutil.disk_usage(settings.BASE_DIR)
                result['metadata']['project_disk_percent'] = project_disk.percent
        
        except Exception as e:
            result['status'] = 'unhealthy'
            result['message'] = f"Disk check failed: {str(e)}"
        
        return result
    
    def check_memory(self):
        """Check system memory usage"""
        result = {
            'status': 'healthy',
            'message': 'Sufficient memory available',
            'metadata': {}
        }
        
        try:
            # Get memory usage
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Convert to human-readable format
            total_mb = memory.total / (1024 * 1024)
            available_mb = memory.available / (1024 * 1024)
            used_mb = memory.used / (1024 * 1024)
            
            result['metadata'] = {
                'total_mb': round(total_mb, 2),
                'available_mb': round(available_mb, 2),
                'used_mb': round(used_mb, 2),
                'percent': memory.percent,
                'swap_percent': swap.percent,
                'swap_total_mb': round(swap.total / (1024 * 1024), 2),
                'swap_used_mb': round(swap.used / (1024 * 1024), 2)
            }
            
            # Check thresholds
            if memory.percent > 90:
                result['status'] = 'unhealthy'
                result['message'] = f"Memory usage critical: {memory.percent}%"
            elif memory.percent > 80:
                result['status'] = 'warning'
                result['message'] = f"Memory usage high: {memory.percent}%"
            
            # Check swap usage if significant swap is configured
            if swap.total > 1024 * 1024 * 1024:  # More than 1GB swap
                if swap.percent > 80:
                    result['status'] = 'warning'
                    result['message'] = f"Swap usage high: {swap.percent}%"
        
        except Exception as e:
            result['status'] = 'unhealthy'
            result['message'] = f"Memory check failed: {str(e)}"
        
        return result
    
    def check_cpu(self):
        """Check CPU usage"""
        result = {
            'status': 'healthy',
            'message': 'CPU load normal',
            'metadata': {}
        }
        
        try:
            # Get CPU info
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_times = psutil.cpu_times()
            
            result['metadata'] = {
                'percent': cpu_percent,
                'count': cpu_count,
                'user': cpu_times.user,
                'system': cpu_times.system,
                'idle': cpu_times.idle
            }
            
            # Check thresholds
            if cpu_percent > 90:
                result['status'] = 'unhealthy'
                result['message'] = f"CPU usage critical: {cpu_percent}%"
            elif cpu_percent > 80:
                result['status'] = 'warning'
                result['message'] = f"CPU usage high: {cpu_percent}%"
            
            # Check load average on Unix systems
            try:
                load1, load5, load15 = psutil.getloadavg()
                result['metadata']['load_avg_1min'] = load1
                result['metadata']['load_avg_5min'] = load5
                result['metadata']['load_avg_15min'] = load15
                
                # Check if load average exceeds number of CPUs
                if load5 > cpu_count * 1.5:
                    result['status'] = 'warning'
                    result['message'] = f"Load average high: {load5} (CPUs: {cpu_count})"
            except:
                pass  # Skip on systems without load average
        
        except Exception as e:
            result['status'] = 'unhealthy'
            result['message'] = f"CPU check failed: {str(e)}"
        
        return result
    
    def check_celery(self):
        """Check Celery workers"""
        result = {
            'status': 'skipped',
            'message': 'Celery check skipped',
            'metadata': {}
        }
        
        # Skip if Celery is not configured
        if 'django_celery_results' not in settings.INSTALLED_APPS:
            return result
        
        try:
            from celery.task.control import inspect
            insp = inspect()
            
            # Check for active workers
            active_workers = insp.ping()
            
            if not active_workers:
                result['status'] = 'unhealthy'
                result['message'] = 'No Celery workers are running'
                return result
            
            # Get worker stats
            active_tasks = insp.active()
            scheduled_tasks = insp.scheduled()
            reserved_tasks = insp.reserved()
            
            result['status'] = 'healthy'
            result['message'] = f"{len(active_workers)} Celery workers running"
            result['metadata'] = {
                'worker_count': len(active_workers),
                'active_tasks': sum(len(tasks) for tasks in active_tasks.values()) if active_tasks else 0,
                'scheduled_tasks': sum(len(tasks) for tasks in scheduled_tasks.values()) if scheduled_tasks else 0,
                'reserved_tasks': sum(len(tasks) for tasks in reserved_tasks.values()) if reserved_tasks else 0,
            }
            
            # Check for overloaded workers
            if active_tasks:
                for worker, tasks in active_tasks.items():
                    if len(tasks) > 10:  # Arbitrary threshold
                        result['status'] = 'warning'
                        result['message'] = f"Worker {worker} has {len(tasks)} active tasks"
        
        except Exception as e:
            result['status'] = 'unhealthy'
            result['message'] = f"Celery check failed: {str(e)}"
        
        return result
    
    def save_health_check_results(self, results):
        """Save health check results to database"""
        try:
            # Save individual check results
            for check_type, check_result in results['checks'].items():
                HealthCheckResult.objects.create(
                    check_type=check_type,
                    status=check_result['status'],
                    message=check_result['message'],
                    metadata=check_result['metadata']
                )
            
            # Save overall system health
            HealthCheckResult.objects.create(
                check_type='system',
                status=results['overall_status'],
                message=f"Overall system health: {results['overall_status']}",
                metadata={
                    'checks_performed': len(results['checks']),
                    'unhealthy_count': sum(1 for check in results['checks'].values() if check['status'] == 'unhealthy'),
                    'warning_count': sum(1 for check in results['checks'].values() if check['status'] == 'warning'),
                    'healthy_count': sum(1 for check in results['checks'].values() if check['status'] == 'healthy')
                }
            )
            
            # Save key metrics
            if 'cpu' in results['checks'] and results['checks']['cpu']['status'] != 'unhealthy':
                SystemMetric.objects.create(
                    name='cpu_percent',
                    value=results['checks']['cpu']['metadata']['percent'],
                    unit='%',
                    category='cpu'
                )
            
            if 'memory' in results['checks'] and results['checks']['memory']['status'] != 'unhealthy':
                SystemMetric.objects.create(
                    name='memory_percent',
                    value=results['checks']['memory']['metadata']['percent'],
                    unit='%',
                    category='memory'
                )
            
            if 'disk' in results['checks'] and results['checks']['disk']['status'] != 'unhealthy':
                SystemMetric.objects.create(
                    name='disk_percent',
                    value=results['checks']['disk']['metadata']['percent'],
                    unit='%',
                    category='disk'
                )
            
            self.stdout.write(self.style.SUCCESS('Health check results saved to database'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error saving health check results: {e}"))
    
    def output_text_results(self, results):
        """Output health check results in text format"""
        self.stdout.write(f"\nSystem Health Check Results - {results['timestamp']}")
        self.stdout.write("=" * 80)
        self.stdout.write(f"Overall Status: {self._colorize_status(results['overall_status'])}")
        self.stdout.write("=" * 80)
        
        for check_type, check_result in results['checks'].items():
            self.stdout.write(f"\n{check_type.upper()}:")
            self.stdout.write(f"  Status: {self._colorize_status(check_result['status'])}")
            self.stdout.write(f"  Message: {check_result['message']}")
            
            if check_result['metadata']:
                self.stdout.write("  Details:")
                for key, value in check_result['metadata'].items():
                    self.stdout.write(f"    {key}: {value}")
        
        self.stdout.write("\n" + "=" * 80)
    
    def _colorize_status(self, status):
        """Add color to status text"""
        if status == 'healthy':
            return self.style.SUCCESS(status.upper())
        elif status == 'warning':
            return self.style.WARNING(status.upper())
        elif status == 'unhealthy':
            return self.style.ERROR(status.upper())
        else:
            return status.upper()