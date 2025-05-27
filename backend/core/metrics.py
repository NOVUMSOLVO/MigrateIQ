"""
Prometheus metrics collection for MigrateIQ.

This module provides comprehensive metrics collection including:
- Application performance metrics
- Business metrics
- Infrastructure metrics
- Custom metrics for monitoring
"""

import time
import logging
from typing import Dict, Any, Optional
from functools import wraps

from django.conf import settings
from django.db import connection
from django.core.cache import cache
from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest
from prometheus_client.multiprocess import MultiProcessCollector

logger = logging.getLogger(__name__)

# Create custom registry for MigrateIQ metrics
REGISTRY = CollectorRegistry()

# Application Performance Metrics
REQUEST_COUNT = Counter(
    'migrateiq_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code'],
    registry=REGISTRY
)

REQUEST_DURATION = Histogram(
    'migrateiq_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, float('inf')),
    registry=REGISTRY
)

# Database Metrics
DB_QUERY_COUNT = Counter(
    'migrateiq_db_queries_total',
    'Total database queries',
    ['operation'],
    registry=REGISTRY
)

DB_QUERY_DURATION = Histogram(
    'migrateiq_db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation'],
    registry=REGISTRY
)

DB_CONNECTION_COUNT = Gauge(
    'migrateiq_db_connections_active',
    'Active database connections',
    registry=REGISTRY
)

# Cache Metrics
CACHE_OPERATIONS = Counter(
    'migrateiq_cache_operations_total',
    'Total cache operations',
    ['operation', 'result'],
    registry=REGISTRY
)

CACHE_HIT_RATE = Gauge(
    'migrateiq_cache_hit_rate',
    'Cache hit rate percentage',
    registry=REGISTRY
)

# Task Queue Metrics
TASK_COUNT = Counter(
    'migrateiq_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status'],
    registry=REGISTRY
)

TASK_DURATION = Histogram(
    'migrateiq_task_duration_seconds',
    'Task execution duration in seconds',
    ['task_name'],
    registry=REGISTRY
)

TASK_QUEUE_SIZE = Gauge(
    'migrateiq_task_queue_size',
    'Number of tasks in queue',
    ['queue_name'],
    registry=REGISTRY
)

# Business Metrics
USER_COUNT = Gauge(
    'migrateiq_users_total',
    'Total number of users',
    ['status'],
    registry=REGISTRY
)

PROJECT_COUNT = Gauge(
    'migrateiq_projects_total',
    'Total number of projects',
    ['status'],
    registry=REGISTRY
)

MIGRATION_COUNT = Counter(
    'migrateiq_migrations_total',
    'Total number of migrations',
    ['status'],
    registry=REGISTRY
)

DATA_VOLUME = Counter(
    'migrateiq_data_volume_bytes',
    'Total data volume processed',
    ['operation'],
    registry=REGISTRY
)

# System Metrics
MEMORY_USAGE = Gauge(
    'migrateiq_memory_usage_bytes',
    'Memory usage in bytes',
    ['type'],
    registry=REGISTRY
)

ERROR_COUNT = Counter(
    'migrateiq_errors_total',
    'Total number of errors',
    ['error_type', 'component'],
    registry=REGISTRY
)

# Application Info
APP_INFO = Info(
    'migrateiq_app_info',
    'Application information',
    registry=REGISTRY
)


class MetricsCollector:
    """Central metrics collector for MigrateIQ."""
    
    def __init__(self):
        self.enabled = getattr(settings, 'METRICS_ENABLED', True)
        self.collect_interval = getattr(settings, 'METRICS_COLLECT_INTERVAL', 60)
        
        # Set application info
        APP_INFO.info({
            'version': getattr(settings, 'VERSION', '1.0.0'),
            'environment': getattr(settings, 'ENVIRONMENT', 'development'),
            'debug': str(settings.DEBUG)
        })
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics."""
        if not self.enabled:
            return
        
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()
        
        REQUEST_DURATION.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_db_query(self, operation: str, duration: float):
        """Record database query metrics."""
        if not self.enabled:
            return
        
        DB_QUERY_COUNT.labels(operation=operation).inc()
        DB_QUERY_DURATION.labels(operation=operation).observe(duration)
    
    def record_cache_operation(self, operation: str, result: str):
        """Record cache operation metrics."""
        if not self.enabled:
            return
        
        CACHE_OPERATIONS.labels(
            operation=operation,
            result=result
        ).inc()
    
    def record_task(self, task_name: str, status: str, duration: Optional[float] = None):
        """Record Celery task metrics."""
        if not self.enabled:
            return
        
        TASK_COUNT.labels(
            task_name=task_name,
            status=status
        ).inc()
        
        if duration is not None:
            TASK_DURATION.labels(task_name=task_name).observe(duration)
    
    def record_error(self, error_type: str, component: str):
        """Record error metrics."""
        if not self.enabled:
            return
        
        ERROR_COUNT.labels(
            error_type=error_type,
            component=component
        ).inc()
    
    def update_business_metrics(self):
        """Update business-related metrics."""
        if not self.enabled:
            return
        
        try:
            from django.contrib.auth import get_user_model
            from core.models import Tenant
            
            User = get_user_model()
            
            # Update user counts
            active_users = User.objects.filter(is_active=True).count()
            inactive_users = User.objects.filter(is_active=False).count()
            
            USER_COUNT.labels(status='active').set(active_users)
            USER_COUNT.labels(status='inactive').set(inactive_users)
            
            # Update tenant counts
            active_tenants = Tenant.objects.filter(is_active=True).count()
            inactive_tenants = Tenant.objects.filter(is_active=False).count()
            
            PROJECT_COUNT.labels(status='active').set(active_tenants)
            PROJECT_COUNT.labels(status='inactive').set(inactive_tenants)
            
        except Exception as e:
            logger.error(f"Error updating business metrics: {e}")
    
    def update_system_metrics(self):
        """Update system-related metrics."""
        if not self.enabled:
            return
        
        try:
            import psutil
            
            # Memory usage
            memory = psutil.virtual_memory()
            MEMORY_USAGE.labels(type='used').set(memory.used)
            MEMORY_USAGE.labels(type='available').set(memory.available)
            MEMORY_USAGE.labels(type='total').set(memory.total)
            
            # Database connections
            db_connections = len(connection.queries)
            DB_CONNECTION_COUNT.set(db_connections)
            
        except ImportError:
            logger.warning("psutil not available for system metrics")
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
    
    def update_cache_metrics(self):
        """Update cache-related metrics."""
        if not self.enabled:
            return
        
        try:
            from core.cache import cache_manager
            
            stats = cache_manager.get_cache_stats()
            hit_rate = stats.get('cache_hit_rate', 0)
            
            CACHE_HIT_RATE.set(hit_rate)
            
        except Exception as e:
            logger.error(f"Error updating cache metrics: {e}")
    
    def collect_all_metrics(self):
        """Collect all metrics."""
        if not self.enabled:
            return
        
        self.update_business_metrics()
        self.update_system_metrics()
        self.update_cache_metrics()


# Global metrics collector instance
metrics_collector = MetricsCollector()


def track_request_metrics(func):
    """Decorator to track request metrics."""
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        start_time = time.time()
        
        try:
            response = func(request, *args, **kwargs)
            status_code = getattr(response, 'status_code', 200)
        except Exception as e:
            status_code = 500
            metrics_collector.record_error(
                error_type=type(e).__name__,
                component='view'
            )
            raise
        finally:
            duration = time.time() - start_time
            metrics_collector.record_request(
                method=request.method,
                endpoint=request.path,
                status_code=status_code,
                duration=duration
            )
        
        return response
    return wrapper


def track_db_metrics(func):
    """Decorator to track database operation metrics."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        operation = func.__name__
        
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            metrics_collector.record_error(
                error_type=type(e).__name__,
                component='database'
            )
            raise
        finally:
            duration = time.time() - start_time
            metrics_collector.record_db_query(operation, duration)
        
        return result
    return wrapper


def track_task_metrics(func):
    """Decorator to track Celery task metrics."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        task_name = func.__name__
        
        try:
            result = func(*args, **kwargs)
            status = 'success'
        except Exception as e:
            status = 'failure'
            metrics_collector.record_error(
                error_type=type(e).__name__,
                component='celery'
            )
            raise
        finally:
            duration = time.time() - start_time
            metrics_collector.record_task(task_name, status, duration)
        
        return result
    return wrapper


class MetricsMiddleware:
    """Middleware to automatically collect request metrics."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        try:
            response = self.get_response(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            metrics_collector.record_error(
                error_type=type(e).__name__,
                component='middleware'
            )
            raise
        finally:
            duration = time.time() - start_time
            
            # Only track API requests
            if request.path.startswith('/api/'):
                metrics_collector.record_request(
                    method=request.method,
                    endpoint=self._normalize_endpoint(request.path),
                    status_code=status_code,
                    duration=duration
                )
        
        return response
    
    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint path for metrics."""
        # Replace IDs with placeholders to avoid high cardinality
        import re
        
        # Replace UUIDs
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/', '/{uuid}/', path)
        
        # Replace numeric IDs
        path = re.sub(r'/\d+/', '/{id}/', path)
        
        return path


def get_metrics():
    """Get all metrics in Prometheus format."""
    if getattr(settings, 'PROMETHEUS_MULTIPROC_DIR', None):
        # Multi-process mode
        registry = CollectorRegistry()
        MultiProcessCollector(registry)
        return generate_latest(registry)
    else:
        # Single process mode
        return generate_latest(REGISTRY)
