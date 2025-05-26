import time
import os
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.conf import settings
from django.db.models import Avg, Max, Min, Count, Sum

from monitoring.models import SystemMetric, TenantMetric, PerformanceLog, Alert, HealthCheckResult
from core.models import Tenant


class Command(BaseCommand):
    help = 'Export system and tenant metrics in Prometheus format'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            dest='metric_type',
            default='all',
            choices=['all', 'system', 'tenant', 'performance', 'health'],
            help='Type of metrics to export',
        )
        parser.add_argument(
            '--output',
            dest='output_file',
            type=str,
            help='Output file path (if not specified, prints to stdout)',
        )
        parser.add_argument(
            '--tenant',
            dest='tenant_id',
            type=str,
            help='Export metrics for specific tenant ID',
        )
    
    def handle(self, *args, **options):
        metric_type = options['metric_type']
        output_file = options['output_file']
        tenant_id = options['tenant_id']
        
        self.stdout.write(self.style.SUCCESS(f'Exporting {metric_type} metrics in Prometheus format...'))
        
        # Generate metrics based on type
        try:
            metrics_text = []
            
            # Add timestamp
            current_time = int(time.time())
            
            if metric_type in ['all', 'system']:
                metrics_text.extend(self.export_system_metrics(current_time))
            
            if metric_type in ['all', 'tenant']:
                metrics_text.extend(self.export_tenant_metrics(current_time, tenant_id))
            
            if metric_type in ['all', 'performance']:
                metrics_text.extend(self.export_performance_metrics(current_time, tenant_id))
            
            if metric_type in ['all', 'health']:
                metrics_text.extend(self.export_health_metrics(current_time))
            
            # Output metrics
            metrics_output = '\n'.join(metrics_text)
            
            if output_file:
                self.output_to_file(metrics_output, output_file)
            else:
                self.stdout.write(metrics_output)
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error exporting metrics: {e}"))
            raise CommandError(f"Metrics export failed: {e}")
    
    def export_system_metrics(self, timestamp):
        """Export system metrics in Prometheus format"""
        metrics = []
        
        # Add metric type headers with descriptions
        metrics.append('# HELP migrateiq_system_cpu CPU usage metrics')
        metrics.append('# TYPE migrateiq_system_cpu gauge')
        metrics.append('# HELP migrateiq_system_memory Memory usage metrics in bytes')
        metrics.append('# TYPE migrateiq_system_memory gauge')
        metrics.append('# HELP migrateiq_system_disk Disk usage metrics in bytes')
        metrics.append('# TYPE migrateiq_system_disk gauge')
        metrics.append('# HELP migrateiq_system_network Network metrics in bytes')
        metrics.append('# TYPE migrateiq_system_network gauge')
        metrics.append('# HELP migrateiq_system_database Database metrics')
        metrics.append('# TYPE migrateiq_system_database gauge')
        metrics.append('# HELP migrateiq_system_redis Redis metrics')
        metrics.append('# TYPE migrateiq_system_redis gauge')
        
        # Get latest system metrics
        latest_metrics = {}
        for metric in SystemMetric.objects.all().order_by('category', 'name', '-created_at').distinct('category', 'name'):
            key = f"{metric.category}_{metric.name}"
            if key not in latest_metrics:
                latest_metrics[key] = metric
        
        # Format metrics in Prometheus format
        for key, metric in latest_metrics.items():
            # Skip metrics with non-numeric values
            try:
                float(metric.value)
            except (ValueError, TypeError):
                continue
                
            # Format: metric_name{label="value",...} value timestamp
            metric_name = f"migrateiq_system_{metric.category}"
            labels = f'name="{metric.name}"'
            
            # Add unit as a label if available
            if metric.unit:
                labels += f',unit="{metric.unit}"'
                
            metrics.append(f"{metric_name}{{{labels}}} {metric.value} {timestamp}")
        
        return metrics
    
    def export_tenant_metrics(self, timestamp, tenant_id=None):
        """Export tenant metrics in Prometheus format"""
        metrics = []
        
        # Add metric type headers with descriptions
        metrics.append('# HELP migrateiq_tenant_users User metrics per tenant')
        metrics.append('# TYPE migrateiq_tenant_users gauge')
        metrics.append('# HELP migrateiq_tenant_storage Storage metrics per tenant in bytes')
        metrics.append('# TYPE migrateiq_tenant_storage gauge')
        metrics.append('# HELP migrateiq_tenant_api_usage API usage metrics per tenant')
        metrics.append('# TYPE migrateiq_tenant_api_usage gauge')
        metrics.append('# HELP migrateiq_tenant_performance Performance metrics per tenant')
        metrics.append('# TYPE migrateiq_tenant_performance gauge')
        
        # Filter by tenant if specified
        tenant_filter = {}
        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id)
                tenant_filter['tenant'] = tenant
            except Tenant.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Tenant with ID {tenant_id} not found"))
                return metrics
        
        # Get latest tenant metrics
        latest_metrics = {}
        query = TenantMetric.objects.filter(**tenant_filter)
        
        # Use distinct on PostgreSQL or manual filtering for other databases
        try:
            for metric in query.order_by('tenant', 'category', 'name', '-created_at').distinct('tenant', 'category', 'name'):
                key = f"{metric.tenant.id}_{metric.category}_{metric.name}"
                if key not in latest_metrics:
                    latest_metrics[key] = metric
        except NotImplementedError:
            # For databases that don't support distinct on fields
            seen_keys = set()
            for metric in query.order_by('tenant', 'category', 'name', '-created_at'):
                key = f"{metric.tenant.id}_{metric.category}_{metric.name}"
                if key not in seen_keys:
                    latest_metrics[key] = metric
                    seen_keys.add(key)
        
        # Format metrics in Prometheus format
        for key, metric in latest_metrics.items():
            # Skip metrics with non-numeric values
            try:
                float(metric.value)
            except (ValueError, TypeError):
                continue
                
            # Format: metric_name{label="value",...} value timestamp
            metric_name = f"migrateiq_tenant_{metric.category}"
            labels = f'tenant="{metric.tenant.name}",tenant_id="{metric.tenant.id}",name="{metric.name}"'
            
            # Add unit as a label if available
            if metric.unit:
                labels += f',unit="{metric.unit}"'
                
            metrics.append(f"{metric_name}{{{labels}}} {metric.value} {timestamp}")
        
        return metrics
    
    def export_performance_metrics(self, timestamp, tenant_id=None):
        """Export performance metrics in Prometheus format"""
        metrics = []
        
        # Add metric type headers with descriptions
        metrics.append('# HELP migrateiq_performance_duration_ms Operation duration in milliseconds')
        metrics.append('# TYPE migrateiq_performance_duration_ms histogram')
        metrics.append('# HELP migrateiq_performance_error_count Error count by operation type')
        metrics.append('# TYPE migrateiq_performance_error_count counter')
        
        # Filter by tenant if specified
        tenant_filter = {}
        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id)
                tenant_filter['tenant'] = tenant
            except Tenant.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Tenant with ID {tenant_id} not found"))
                return metrics
        
        # Get performance metrics aggregated by operation type
        operation_types = PerformanceLog.objects.filter(**tenant_filter).values_list('operation_type', flat=True).distinct()
        
        for op_type in operation_types:
            # Get logs for this operation type
            logs = PerformanceLog.objects.filter(operation_type=op_type, **tenant_filter)
            
            # Calculate metrics
            avg_duration = logs.aggregate(avg=Avg('duration_ms'))['avg'] or 0
            max_duration = logs.aggregate(max=Max('duration_ms'))['max'] or 0
            error_count = logs.filter(status='error').count()
            success_count = logs.filter(status='success').count()
            total_count = logs.count()
            
            # Add tenant label if filtering by tenant
            tenant_label = ''
            if tenant_id and 'tenant' in tenant_filter:
                tenant = tenant_filter['tenant']
                tenant_label = f',tenant="{tenant.name}",tenant_id="{tenant.id}"'
            
            # Format metrics
            metrics.append(f"migrateiq_performance_duration_ms{{operation="{op_type}",type="avg"{tenant_label}}} {avg_duration} {timestamp}")
            metrics.append(f"migrateiq_performance_duration_ms{{operation="{op_type}",type="max"{tenant_label}}} {max_duration} {timestamp}")
            metrics.append(f"migrateiq_performance_error_count{{operation="{op_type}"{tenant_label}}} {error_count} {timestamp}")
            
            # Add success rate as a percentage
            if total_count > 0:
                success_rate = (success_count / total_count) * 100
                metrics.append(f"migrateiq_performance_success_rate{{operation="{op_type}"{tenant_label}}} {success_rate} {timestamp}")
        
        return metrics
    
    def export_health_metrics(self, timestamp):
        """Export health check metrics in Prometheus format"""
        metrics = []
        
        # Add metric type headers with descriptions
        metrics.append('# HELP migrateiq_health_status Health check status (0=unhealthy, 1=warning, 2=healthy)')
        metrics.append('# TYPE migrateiq_health_status gauge')
        metrics.append('# HELP migrateiq_health_uptime_percent Uptime percentage by component')
        metrics.append('# TYPE migrateiq_health_uptime_percent gauge')
        
        # Get latest health check results by component
        check_types = HealthCheckResult.objects.values_list('check_type', flat=True).distinct()
        
        for check_type in check_types:
            # Get latest check for this type
            latest = HealthCheckResult.objects.filter(check_type=check_type).order_by('-created_at').first()
            
            if latest:
                # Convert status to numeric value
                status_value = 2 if latest.status == 'healthy' else 1 if latest.status == 'warning' else 0
                
                # Format metric
                metrics.append(f"migrateiq_health_status{{component="{check_type}"}} {status_value} {timestamp}")
                
                # Calculate uptime percentage for this component
                total_checks = HealthCheckResult.objects.filter(check_type=check_type).count()
                healthy_checks = HealthCheckResult.objects.filter(check_type=check_type, status='healthy').count()
                
                if total_checks > 0:
                    uptime_pct = (healthy_checks / total_checks) * 100
                    metrics.append(f"migrateiq_health_uptime_percent{{component="{check_type}"}} {uptime_pct} {timestamp}")
        
        # Add overall system health status
        latest_system = HealthCheckResult.objects.filter(check_type='system').order_by('-created_at').first()
        if latest_system:
            status_value = 2 if latest_system.status == 'healthy' else 1 if latest_system.status == 'warning' else 0
            metrics.append(f"migrateiq_health_status{{component="overall"}} {status_value} {timestamp}")
        
        return metrics
    
    def output_to_file(self, metrics_text, file_path):
        """Output metrics to a file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            with open(file_path, 'w') as f:
                f.write(metrics_text)
            
            self.stdout.write(self.style.SUCCESS(f"Metrics saved to {file_path}"))
        except Exception as e:
            raise CommandError(f"Failed to write to file: {e}")