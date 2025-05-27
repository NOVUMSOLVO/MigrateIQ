"""
Django management command for Celery task management.

Usage:
    python manage.py celery_management --stats
    python manage.py celery_management --cleanup
    python manage.py celery_management --monitor
    python manage.py celery_management --purge-queue queue_name
"""

import json
import time
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from celery import Celery
from celery.result import AsyncResult
from core.celery_monitoring import task_monitor, result_manager


class Command(BaseCommand):
    help = 'Manage Celery tasks and queues for MigrateIQ'

    def add_arguments(self, parser):
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show comprehensive task statistics',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up old task results',
        )
        parser.add_argument(
            '--cleanup-hours',
            type=int,
            default=24,
            help='Clean up results older than specified hours (default: 24)',
        )
        parser.add_argument(
            '--monitor',
            action='store_true',
            help='Monitor task execution in real-time',
        )
        parser.add_argument(
            '--purge-queue',
            type=str,
            help='Purge all tasks from specified queue',
        )
        parser.add_argument(
            '--list-active',
            action='store_true',
            help='List currently active tasks',
        )
        parser.add_argument(
            '--list-scheduled',
            action='store_true',
            help='List scheduled tasks',
        )
        parser.add_argument(
            '--revoke-task',
            type=str,
            help='Revoke a specific task by ID',
        )
        parser.add_argument(
            '--inspect-workers',
            action='store_true',
            help='Inspect worker status',
        )

    def handle(self, *args, **options):
        if options['stats']:
            self.show_task_stats()
        elif options['cleanup']:
            self.cleanup_old_results(options['cleanup_hours'])
        elif options['monitor']:
            self.monitor_tasks()
        elif options['purge_queue']:
            self.purge_queue(options['purge_queue'])
        elif options['list_active']:
            self.list_active_tasks()
        elif options['list_scheduled']:
            self.list_scheduled_tasks()
        elif options['revoke_task']:
            self.revoke_task(options['revoke_task'])
        elif options['inspect_workers']:
            self.inspect_workers()
        else:
            self.stdout.write(
                self.style.ERROR('Please specify an action. Use --help for available options.')
            )

    def show_task_stats(self):
        """Display comprehensive task statistics."""
        self.stdout.write(self.style.SUCCESS('=== Celery Task Statistics ==='))
        
        try:
            # Get task metrics
            metrics = task_monitor.get_task_metrics()
            
            if not metrics:
                self.stdout.write(self.style.WARNING('No task metrics available'))
                return
            
            # Display counters
            self.stdout.write('\n--- Task Counters ---')
            for key, value in metrics.items():
                if key.startswith('counter_'):
                    counter_name = key.replace('counter_', '').replace('_', ' ').title()
                    self.stdout.write(f"{counter_name}: {value}")
            
            # Display runtime statistics
            runtime_stats = metrics.get('runtime_stats', {})
            if runtime_stats:
                self.stdout.write('\n--- Runtime Statistics ---')
                for task_name, stats in runtime_stats.items():
                    self.stdout.write(f"\n{task_name}:")
                    self.stdout.write(f"  Count: {stats['count']}")
                    self.stdout.write(f"  Avg Time: {stats['avg_time']:.2f}s")
                    self.stdout.write(f"  Min Time: {stats['min_time']:.2f}s")
                    self.stdout.write(f"  Max Time: {stats['max_time']:.2f}s")
            
            # Display recent failures
            recent_failures = metrics.get('recent_failures', [])
            if recent_failures:
                self.stdout.write('\n--- Recent Failures ---')
                for failure in recent_failures[:5]:  # Show last 5
                    parts = failure.split(':')
                    if len(parts) >= 3:
                        task_id, task_name, exception = parts[0], parts[1], parts[2]
                        self.stdout.write(f"  {task_name} ({task_id[:8]}...): {exception}")
            
            # Get result statistics
            result_stats = result_manager.get_task_result_stats()
            if result_stats:
                self.stdout.write('\n--- Result Statistics ---')
                self.stdout.write(f"Total Results: {result_stats.get('total_results', 0)}")
                self.stdout.write(f"Average Result Size: {result_stats.get('avg_result_size', 0)} bytes")
                
                status_counts = result_stats.get('status_counts', {})
                if status_counts:
                    self.stdout.write('Status Distribution:')
                    for status, count in status_counts.items():
                        self.stdout.write(f"  {status}: {count}")
                
                if result_stats.get('oldest_result'):
                    self.stdout.write(f"Oldest Result: {result_stats['oldest_result']}")
                if result_stats.get('newest_result'):
                    self.stdout.write(f"Newest Result: {result_stats['newest_result']}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error retrieving task stats: {e}"))

    def cleanup_old_results(self, hours: int):
        """Clean up old task results."""
        self.stdout.write(self.style.SUCCESS(f'=== Cleaning up results older than {hours} hours ==='))
        
        try:
            cleaned_count = result_manager.cleanup_old_results(hours)
            self.stdout.write(
                self.style.SUCCESS(f"✓ Cleaned up {cleaned_count} old task results")
            )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Cleanup failed: {e}"))

    def monitor_tasks(self):
        """Monitor task execution in real-time."""
        self.stdout.write(self.style.SUCCESS('=== Real-time Task Monitor ==='))
        self.stdout.write('Press Ctrl+C to stop monitoring\n')
        
        try:
            last_metrics = {}
            
            while True:
                current_metrics = task_monitor.get_task_metrics()
                
                # Clear screen and show current stats
                self.stdout.write('\033[2J\033[H')  # Clear screen
                self.stdout.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Show task counters with deltas
                self.stdout.write('\n--- Task Activity ---')
                for key, value in current_metrics.items():
                    if key.startswith('counter_'):
                        counter_name = key.replace('counter_', '').replace('_', ' ').title()
                        last_value = last_metrics.get(key, 0)
                        delta = value - last_value
                        delta_str = f" (+{delta})" if delta > 0 else ""
                        self.stdout.write(f"{counter_name}: {value}{delta_str}")
                
                # Show recent runtime stats
                runtime_stats = current_metrics.get('runtime_stats', {})
                if runtime_stats:
                    self.stdout.write('\n--- Recent Task Performance ---')
                    for task_name, stats in list(runtime_stats.items())[:5]:  # Show top 5
                        self.stdout.write(
                            f"{task_name}: {stats['count']} runs, "
                            f"avg {stats['avg_time']:.2f}s"
                        )
                
                last_metrics = current_metrics
                time.sleep(5)  # Update every 5 seconds
                
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('\nMonitoring stopped'))

    def purge_queue(self, queue_name: str):
        """Purge all tasks from specified queue."""
        self.stdout.write(self.style.WARNING(f'=== Purging queue: {queue_name} ==='))
        
        try:
            from celery import current_app
            
            # Get queue length before purging
            inspect = current_app.control.inspect()
            active_queues = inspect.active_queues()
            
            if not active_queues:
                self.stdout.write(self.style.WARNING('No active workers found'))
                return
            
            # Purge the queue
            current_app.control.purge()
            self.stdout.write(self.style.SUCCESS(f"✓ Purged queue '{queue_name}'"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Queue purge failed: {e}"))

    def list_active_tasks(self):
        """List currently active tasks."""
        self.stdout.write(self.style.SUCCESS('=== Active Tasks ==='))
        
        try:
            from celery import current_app
            
            inspect = current_app.control.inspect()
            active_tasks = inspect.active()
            
            if not active_tasks:
                self.stdout.write('No active tasks found')
                return
            
            for worker, tasks in active_tasks.items():
                self.stdout.write(f"\nWorker: {worker}")
                if not tasks:
                    self.stdout.write("  No active tasks")
                    continue
                
                for task in tasks:
                    task_id = task.get('id', 'Unknown')
                    task_name = task.get('name', 'Unknown')
                    args = task.get('args', [])
                    kwargs = task.get('kwargs', {})
                    
                    self.stdout.write(f"  Task: {task_name}")
                    self.stdout.write(f"    ID: {task_id}")
                    self.stdout.write(f"    Args: {args}")
                    self.stdout.write(f"    Kwargs: {kwargs}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error listing active tasks: {e}"))

    def list_scheduled_tasks(self):
        """List scheduled tasks."""
        self.stdout.write(self.style.SUCCESS('=== Scheduled Tasks ==='))
        
        try:
            from celery import current_app
            
            inspect = current_app.control.inspect()
            scheduled_tasks = inspect.scheduled()
            
            if not scheduled_tasks:
                self.stdout.write('No scheduled tasks found')
                return
            
            for worker, tasks in scheduled_tasks.items():
                self.stdout.write(f"\nWorker: {worker}")
                if not tasks:
                    self.stdout.write("  No scheduled tasks")
                    continue
                
                for task in tasks:
                    task_id = task.get('request', {}).get('id', 'Unknown')
                    task_name = task.get('request', {}).get('task', 'Unknown')
                    eta = task.get('eta', 'Unknown')
                    
                    self.stdout.write(f"  Task: {task_name}")
                    self.stdout.write(f"    ID: {task_id}")
                    self.stdout.write(f"    ETA: {eta}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error listing scheduled tasks: {e}"))

    def revoke_task(self, task_id: str):
        """Revoke a specific task."""
        self.stdout.write(self.style.WARNING(f'=== Revoking task: {task_id} ==='))
        
        try:
            from celery import current_app
            
            # Revoke the task
            current_app.control.revoke(task_id, terminate=True)
            
            # Check task status
            result = AsyncResult(task_id)
            self.stdout.write(f"Task status: {result.status}")
            
            self.stdout.write(self.style.SUCCESS(f"✓ Task {task_id} revoked"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Task revocation failed: {e}"))

    def inspect_workers(self):
        """Inspect worker status."""
        self.stdout.write(self.style.SUCCESS('=== Worker Status ==='))
        
        try:
            from celery import current_app
            
            inspect = current_app.control.inspect()
            
            # Get worker stats
            stats = inspect.stats()
            if stats:
                for worker, worker_stats in stats.items():
                    self.stdout.write(f"\nWorker: {worker}")
                    self.stdout.write(f"  Pool: {worker_stats.get('pool', {}).get('implementation', 'Unknown')}")
                    self.stdout.write(f"  Processes: {worker_stats.get('pool', {}).get('processes', 'Unknown')}")
                    self.stdout.write(f"  Total Tasks: {worker_stats.get('total', 'Unknown')}")
                    
                    # Memory info
                    rusage = worker_stats.get('rusage', {})
                    if rusage:
                        self.stdout.write(f"  Memory Usage: {rusage.get('maxrss', 'Unknown')} KB")
            
            # Get registered tasks
            registered = inspect.registered()
            if registered:
                self.stdout.write('\n--- Registered Tasks ---')
                for worker, tasks in registered.items():
                    self.stdout.write(f"\nWorker: {worker}")
                    for task in sorted(tasks):
                        self.stdout.write(f"  {task}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Worker inspection failed: {e}"))
