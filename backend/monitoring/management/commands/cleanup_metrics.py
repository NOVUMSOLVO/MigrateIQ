import os
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.conf import settings
from django.db.models import Count

from monitoring.models import SystemMetric, TenantMetric, PerformanceLog, Alert, HealthCheckResult


class Command(BaseCommand):
    help = 'Clean up old monitoring data based on retention policies'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help='Force cleanup without confirmation',
        )
        parser.add_argument(
            '--system-days',
            dest='system_days',
            type=int,
            default=90,
            help='Number of days to keep system metrics (default: 90)',
        )
        parser.add_argument(
            '--tenant-days',
            dest='tenant_days',
            type=int,
            default=90,
            help='Number of days to keep tenant metrics (default: 90)',
        )
        parser.add_argument(
            '--performance-days',
            dest='performance_days',
            type=int,
            default=30,
            help='Number of days to keep performance logs (default: 30)',
        )
        parser.add_argument(
            '--health-days',
            dest='health_days',
            type=int,
            default=60,
            help='Number of days to keep health check results (default: 60)',
        )
        parser.add_argument(
            '--alerts-days',
            dest='alerts_days',
            type=int,
            default=180,
            help='Number of days to keep resolved alerts (default: 180)',
        )
        parser.add_argument(
            '--keep-critical',
            action='store_true',
            dest='keep_critical',
            default=True,
            help='Keep critical alerts regardless of age',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        system_days = options['system_days']
        tenant_days = options['tenant_days']
        performance_days = options['performance_days']
        health_days = options['health_days']
        alerts_days = options['alerts_days']
        keep_critical = options['keep_critical']
        
        # Calculate cutoff dates
        now = timezone.now()
        system_cutoff = now - timedelta(days=system_days)
        tenant_cutoff = now - timedelta(days=tenant_days)
        performance_cutoff = now - timedelta(days=performance_days)
        health_cutoff = now - timedelta(days=health_days)
        alerts_cutoff = now - timedelta(days=alerts_days)
        
        # Show cleanup plan
        self.stdout.write(self.style.SUCCESS('Cleanup Plan:'))
        self.stdout.write(f"System metrics older than {system_cutoff.date()} ({system_days} days)")
        self.stdout.write(f"Tenant metrics older than {tenant_cutoff.date()} ({tenant_days} days)")
        self.stdout.write(f"Performance logs older than {performance_cutoff.date()} ({performance_days} days)")
        self.stdout.write(f"Health check results older than {health_cutoff.date()} ({health_days} days)")
        self.stdout.write(f"Resolved alerts older than {alerts_cutoff.date()} ({alerts_days} days)")
        if keep_critical:
            self.stdout.write("Critical alerts will be kept regardless of age")
        
        # Count records to be deleted
        system_count = SystemMetric.objects.filter(created_at__lt=system_cutoff).count()
        tenant_count = TenantMetric.objects.filter(created_at__lt=tenant_cutoff).count()
        performance_count = PerformanceLog.objects.filter(created_at__lt=performance_cutoff).count()
        health_count = HealthCheckResult.objects.filter(created_at__lt=health_cutoff).count()
        
        # For alerts, only count resolved ones
        alerts_query = Alert.objects.filter(created_at__lt=alerts_cutoff, resolved=True)
        if keep_critical:
            alerts_query = alerts_query.exclude(level='critical')
        alerts_count = alerts_query.count()
        
        self.stdout.write(self.style.WARNING(f"\nRecords to be deleted:"))
        self.stdout.write(f"System metrics: {system_count}")
        self.stdout.write(f"Tenant metrics: {tenant_count}")
        self.stdout.write(f"Performance logs: {performance_count}")
        self.stdout.write(f"Health check results: {health_count}")
        self.stdout.write(f"Resolved alerts: {alerts_count}")
        
        total_count = system_count + tenant_count + performance_count + health_count + alerts_count
        self.stdout.write(self.style.WARNING(f"\nTotal records to be deleted: {total_count}"))
        
        # Confirm deletion unless --force is used
        if not dry_run and not force:
            confirm = input("\nAre you sure you want to delete these records? [y/N] ")
            if confirm.lower() != 'y':
                self.stdout.write(self.style.SUCCESS("Cleanup cancelled."))
                return
        
        # Perform deletion if not a dry run
        if not dry_run:
            try:
                # Delete in batches to avoid memory issues
                self._delete_in_batches(SystemMetric, {'created_at__lt': system_cutoff})
                self._delete_in_batches(TenantMetric, {'created_at__lt': tenant_cutoff})
                self._delete_in_batches(PerformanceLog, {'created_at__lt': performance_cutoff})
                self._delete_in_batches(HealthCheckResult, {'created_at__lt': health_cutoff})
                
                # For alerts, only delete resolved ones
                alert_filters = {'created_at__lt': alerts_cutoff, 'resolved': True}
                if keep_critical:
                    # Exclude critical alerts
                    self._delete_in_batches(Alert, alert_filters, exclude_filters={'level': 'critical'})
                else:
                    self._delete_in_batches(Alert, alert_filters)
                
                self.stdout.write(self.style.SUCCESS(f"\nSuccessfully deleted {total_count} records."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error during cleanup: {e}"))
                raise CommandError(f"Cleanup failed: {e}")
        else:
            self.stdout.write(self.style.SUCCESS("\nDry run completed. No records were deleted."))
    
    def _delete_in_batches(self, model, filters, exclude_filters=None, batch_size=1000):
        """Delete records in batches to avoid memory issues"""
        queryset = model.objects.filter(**filters)
        if exclude_filters:
            queryset = queryset.exclude(**exclude_filters)
        
        total = queryset.count()
        if total == 0:
            return 0
        
        model_name = model.__name__
        self.stdout.write(f"Deleting {total} {model_name} records in batches of {batch_size}...")
        
        deleted = 0
        while deleted < total:
            # Get primary keys for the next batch
            batch_pks = queryset.values_list('pk', flat=True)[:batch_size]
            if not batch_pks:
                break
                
            # Delete the batch
            batch_qs = model.objects.filter(pk__in=list(batch_pks))
            count, _ = batch_qs.delete()
            deleted += count
            
            # Show progress
            progress = (deleted / total) * 100 if total > 0 else 100
            self.stdout.write(f"  Progress: {deleted}/{total} ({progress:.1f}%)")
        
        return deleted
    
    def _optimize_tables(self):
        """Optimize database tables after large deletions"""
        # This is database-specific and would need to be implemented based on the database being used
        # For example, for MySQL you might use "OPTIMIZE TABLE", for PostgreSQL "VACUUM ANALYZE", etc.
        pass