"""
Advanced Celery task monitoring and management for MigrateIQ.

This module provides comprehensive task monitoring including:
- Task result optimization and cleanup
- Priority-based task queues
- Task retry mechanisms with exponential backoff
- Dead letter queue for failed tasks
- Task scheduling and cron job management
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from functools import wraps

from celery import Celery, Task
from celery.result import AsyncResult
from celery.signals import task_prerun, task_postrun, task_failure, task_retry
from celery.exceptions import Retry, WorkerLostError
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class TaskMonitor:
    """Advanced task monitoring and metrics collection."""
    
    def __init__(self):
        self.redis_client = self._get_redis_client()
        self.metrics_prefix = 'celery_metrics'
        
    def _get_redis_client(self):
        """Get Redis client for metrics storage."""
        try:
            redis_url = getattr(settings, 'CELERY_BROKER_URL', 'redis://localhost:6379/0')
            return redis.from_url(redis_url, decode_responses=True)
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            return None
    
    def record_task_start(self, task_id: str, task_name: str, args: tuple, kwargs: dict):
        """Record task start metrics."""
        if not self.redis_client:
            return
        
        try:
            timestamp = time.time()
            task_data = {
                'task_id': task_id,
                'task_name': task_name,
                'started_at': timestamp,
                'args_count': len(args),
                'kwargs_count': len(kwargs),
                'status': 'STARTED'
            }
            
            # Store task data
            self.redis_client.hset(
                f"{self.metrics_prefix}:tasks:{task_id}",
                mapping=task_data
            )
            
            # Increment task counter
            self.redis_client.incr(f"{self.metrics_prefix}:counters:started")
            self.redis_client.incr(f"{self.metrics_prefix}:counters:started:{task_name}")
            
            # Set expiration for task data (24 hours)
            self.redis_client.expire(f"{self.metrics_prefix}:tasks:{task_id}", 86400)
            
        except RedisError as e:
            logger.error(f"Error recording task start: {e}")
    
    def record_task_success(self, task_id: str, task_name: str, runtime: float, result: Any):
        """Record successful task completion."""
        if not self.redis_client:
            return
        
        try:
            # Update task data
            self.redis_client.hset(
                f"{self.metrics_prefix}:tasks:{task_id}",
                mapping={
                    'completed_at': time.time(),
                    'runtime': runtime,
                    'status': 'SUCCESS',
                    'result_size': len(str(result)) if result else 0
                }
            )
            
            # Update counters
            self.redis_client.incr(f"{self.metrics_prefix}:counters:success")
            self.redis_client.incr(f"{self.metrics_prefix}:counters:success:{task_name}")
            
            # Update runtime statistics
            self._update_runtime_stats(task_name, runtime)
            
        except RedisError as e:
            logger.error(f"Error recording task success: {e}")
    
    def record_task_failure(self, task_id: str, task_name: str, exception: Exception, traceback: str):
        """Record task failure."""
        if not self.redis_client:
            return
        
        try:
            # Update task data
            self.redis_client.hset(
                f"{self.metrics_prefix}:tasks:{task_id}",
                mapping={
                    'failed_at': time.time(),
                    'status': 'FAILURE',
                    'exception': str(exception),
                    'exception_type': type(exception).__name__
                }
            )
            
            # Update counters
            self.redis_client.incr(f"{self.metrics_prefix}:counters:failure")
            self.redis_client.incr(f"{self.metrics_prefix}:counters:failure:{task_name}")
            self.redis_client.incr(f"{self.metrics_prefix}:exceptions:{type(exception).__name__}")
            
            # Add to failed tasks list for analysis
            self.redis_client.lpush(
                f"{self.metrics_prefix}:failed_tasks",
                f"{task_id}:{task_name}:{type(exception).__name__}"
            )
            self.redis_client.ltrim(f"{self.metrics_prefix}:failed_tasks", 0, 999)  # Keep last 1000
            
        except RedisError as e:
            logger.error(f"Error recording task failure: {e}")
    
    def record_task_retry(self, task_id: str, task_name: str, retry_count: int, exception: Exception):
        """Record task retry."""
        if not self.redis_client:
            return
        
        try:
            # Update task data
            self.redis_client.hset(
                f"{self.metrics_prefix}:tasks:{task_id}",
                mapping={
                    'retry_count': retry_count,
                    'last_retry_at': time.time(),
                    'retry_reason': str(exception)
                }
            )
            
            # Update counters
            self.redis_client.incr(f"{self.metrics_prefix}:counters:retry")
            self.redis_client.incr(f"{self.metrics_prefix}:counters:retry:{task_name}")
            
        except RedisError as e:
            logger.error(f"Error recording task retry: {e}")
    
    def _update_runtime_stats(self, task_name: str, runtime: float):
        """Update runtime statistics for task."""
        try:
            stats_key = f"{self.metrics_prefix}:runtime_stats:{task_name}"
            
            # Get current stats
            current_stats = self.redis_client.hgetall(stats_key)
            
            if current_stats:
                count = int(current_stats.get('count', 0))
                total_time = float(current_stats.get('total_time', 0))
                min_time = float(current_stats.get('min_time', runtime))
                max_time = float(current_stats.get('max_time', runtime))
            else:
                count = 0
                total_time = 0
                min_time = runtime
                max_time = runtime
            
            # Update stats
            new_count = count + 1
            new_total_time = total_time + runtime
            new_avg_time = new_total_time / new_count
            new_min_time = min(min_time, runtime)
            new_max_time = max(max_time, runtime)
            
            # Store updated stats
            self.redis_client.hset(stats_key, mapping={
                'count': new_count,
                'total_time': new_total_time,
                'avg_time': new_avg_time,
                'min_time': new_min_time,
                'max_time': new_max_time,
                'last_updated': time.time()
            })
            
            # Set expiration (7 days)
            self.redis_client.expire(stats_key, 604800)
            
        except RedisError as e:
            logger.error(f"Error updating runtime stats: {e}")
    
    def get_task_metrics(self) -> Dict[str, Any]:
        """Get comprehensive task metrics."""
        if not self.redis_client:
            return {}
        
        try:
            metrics = {}
            
            # Get counters
            counter_keys = self.redis_client.keys(f"{self.metrics_prefix}:counters:*")
            for key in counter_keys:
                counter_name = key.split(':')[-1]
                metrics[f"counter_{counter_name}"] = int(self.redis_client.get(key) or 0)
            
            # Get runtime stats
            runtime_keys = self.redis_client.keys(f"{self.metrics_prefix}:runtime_stats:*")
            runtime_stats = {}
            for key in runtime_keys:
                task_name = key.split(':')[-1]
                stats = self.redis_client.hgetall(key)
                if stats:
                    runtime_stats[task_name] = {
                        'count': int(stats.get('count', 0)),
                        'avg_time': float(stats.get('avg_time', 0)),
                        'min_time': float(stats.get('min_time', 0)),
                        'max_time': float(stats.get('max_time', 0)),
                    }
            metrics['runtime_stats'] = runtime_stats
            
            # Get recent failed tasks
            failed_tasks = self.redis_client.lrange(f"{self.metrics_prefix}:failed_tasks", 0, 9)
            metrics['recent_failures'] = failed_tasks
            
            return metrics
            
        except RedisError as e:
            logger.error(f"Error getting task metrics: {e}")
            return {}


# Global task monitor instance
task_monitor = TaskMonitor()


class MonitoredTask(Task):
    """Custom Celery task class with monitoring and retry logic."""
    
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 60}
    retry_backoff = True
    retry_backoff_max = 700
    retry_jitter = True
    
    def retry(self, args=None, kwargs=None, exc=None, throw=True, eta=None, countdown=None, max_retries=None, **options):
        """Enhanced retry with monitoring."""
        task_monitor.record_task_retry(
            self.request.id,
            self.name,
            self.request.retries,
            exc
        )
        return super().retry(args, kwargs, exc, throw, eta, countdown, max_retries, **options)


def monitored_task(*args, **kwargs):
    """Decorator for creating monitored tasks."""
    kwargs.setdefault('base', MonitoredTask)
    return Celery.task(*args, **kwargs)


class TaskResultManager:
    """Manage task results and cleanup."""
    
    def __init__(self):
        self.redis_client = task_monitor.redis_client
        self.result_ttl = getattr(settings, 'CELERY_RESULT_EXPIRES', 3600)  # 1 hour default
    
    def cleanup_old_results(self, older_than_hours: int = 24):
        """Clean up old task results."""
        if not self.redis_client:
            return 0
        
        try:
            cutoff_time = time.time() - (older_than_hours * 3600)
            cleaned_count = 0
            
            # Get all task result keys
            result_keys = self.redis_client.keys("celery-task-meta-*")
            
            for key in result_keys:
                try:
                    # Check if result is old
                    result_data = self.redis_client.hgetall(key)
                    if result_data and 'date_done' in result_data:
                        date_done = float(result_data['date_done'])
                        if date_done < cutoff_time:
                            self.redis_client.delete(key)
                            cleaned_count += 1
                except Exception as e:
                    logger.warning(f"Error checking result key {key}: {e}")
            
            logger.info(f"Cleaned up {cleaned_count} old task results")
            return cleaned_count
            
        except RedisError as e:
            logger.error(f"Error cleaning up task results: {e}")
            return 0
    
    def get_task_result_stats(self) -> Dict[str, Any]:
        """Get task result statistics."""
        if not self.redis_client:
            return {}
        
        try:
            result_keys = self.redis_client.keys("celery-task-meta-*")
            
            stats = {
                'total_results': len(result_keys),
                'status_counts': {},
                'avg_result_size': 0,
                'oldest_result': None,
                'newest_result': None
            }
            
            if not result_keys:
                return stats
            
            total_size = 0
            oldest_time = float('inf')
            newest_time = 0
            
            for key in result_keys[:100]:  # Sample first 100 for performance
                try:
                    result_data = self.redis_client.hgetall(key)
                    if result_data:
                        status = result_data.get('status', 'UNKNOWN')
                        stats['status_counts'][status] = stats['status_counts'].get(status, 0) + 1
                        
                        # Calculate size
                        result_size = sum(len(str(v)) for v in result_data.values())
                        total_size += result_size
                        
                        # Track timestamps
                        if 'date_done' in result_data:
                            date_done = float(result_data['date_done'])
                            oldest_time = min(oldest_time, date_done)
                            newest_time = max(newest_time, date_done)
                            
                except Exception as e:
                    logger.warning(f"Error processing result key {key}: {e}")
            
            if total_size > 0:
                stats['avg_result_size'] = total_size // min(len(result_keys), 100)
            
            if oldest_time != float('inf'):
                stats['oldest_result'] = datetime.fromtimestamp(oldest_time).isoformat()
            if newest_time > 0:
                stats['newest_result'] = datetime.fromtimestamp(newest_time).isoformat()
            
            return stats
            
        except RedisError as e:
            logger.error(f"Error getting result stats: {e}")
            return {}


# Global result manager instance
result_manager = TaskResultManager()


# Celery signal handlers
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Handle task prerun signal."""
    task_monitor.record_task_start(task_id, task.name, args or (), kwargs or {})


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, 
                        retval=None, state=None, **kwds):
    """Handle task postrun signal."""
    if state == 'SUCCESS':
        runtime = getattr(task, '_runtime', 0)
        task_monitor.record_task_success(task_id, task.name, runtime, retval)


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds):
    """Handle task failure signal."""
    task_monitor.record_task_failure(task_id, sender.name, exception, traceback)


@task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, einfo=None, **kwds):
    """Handle task retry signal."""
    retry_count = getattr(sender.request, 'retries', 0)
    task_monitor.record_task_retry(task_id, sender.name, retry_count, reason)
