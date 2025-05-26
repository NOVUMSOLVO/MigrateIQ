import json
import csv
import os
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.conf import settings
from django.db.models import Avg, Max, Min, Count, Sum
from django.core.cache import cache

from monitoring.models import SystemMetric, TenantMetric, PerformanceLog, Alert, HealthCheckResult
from core.models import Tenant


class Command(BaseCommand):
    help = 'Generate comprehensive system and tenant reports'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            dest='report_type',
            default='all',
            choices=['all', 'system', 'tenant', 'performance', 'health'],
            help='Type of report to generate',
        )
        parser.add_argument(
            '--tenant',
            dest='tenant_id',
            type=str,
            help='Generate report for specific tenant ID',
        )
        parser.add_argument(
            '--days',
            dest='days',
            type=int,
            default=30,
            help='Number of days to include in the report',
        )
        parser.add_argument(
            '--format',
            dest='format',
            default='json',
            choices=['json', 'csv', 'text'],
            help='Output format for the report',
        )
        parser.add_argument(
            '--output',
            dest='output_file',
            type=str,
            help='Output file path (if not specified, prints to stdout)',
        )
        parser.add_argument(
            '--cache',
            action='store_true',
            dest='cache_report',
            default=False,
            help='Cache the report results for faster access via API',
        )
    
    def handle(self, *args, **options):
        report_type = options['report_type']
        tenant_id = options['tenant_id']
        days = options['days']
        output_format = options['format']
        output_file = options['output_file']
        cache_report = options['cache_report']
        
        self.stdout.write(self.style.SUCCESS(f'Generating {report_type} report for the past {days} days...'))
        
        # Set time range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Generate report based on type
        try:
            if report_type == 'all':
                report_data = self.generate_all_reports(start_date, end_date, tenant_id)
            elif report_type == 'system':
                report_data = self.generate_system_report(start_date, end_date)
            elif report_type == 'tenant':
                report_data = self.generate_tenant_report(start_date, end_date, tenant_id)
            elif report_type == 'performance':
                report_data = self.generate_performance_report(start_date, end_date, tenant_id)
            elif report_type == 'health':
                report_data = self.generate_health_report(start_date, end_date)
            
            # Add metadata
            report_data['metadata'] = {
                'generated_at': timezone.now().isoformat(),
                'report_type': report_type,
                'period_start': start_date.isoformat(),
                'period_end': end_date.isoformat(),
                'days_included': days
            }
            
            # Cache report if requested
            if cache_report:
                cache_key = f"report:{report_type}:{tenant_id or 'all'}:{days}"
                cache.set(cache_key, report_data, 60 * 60 * 24)  # Cache for 24 hours
                self.stdout.write(self.style.SUCCESS(f"Report cached with key: {cache_key}"))
            
            # Output report
            if output_file:
                self.output_to_file(report_data, output_file, output_format)
            else:
                self.output_to_stdout(report_data, output_format)
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error generating report: {e}"))
            raise CommandError(f"Report generation failed: {e}")
    
    def generate_all_reports(self, start_date, end_date, tenant_id=None):
        """Generate a comprehensive report with all metrics"""
        report = {
            'system': self.generate_system_report(start_date, end_date),
            'health': self.generate_health_report(start_date, end_date),
            'performance': self.generate_performance_report(start_date, end_date, tenant_id)
        }
        
        if tenant_id:
            report['tenant'] = self.generate_tenant_report(start_date, end_date, tenant_id)
        else:
            report['tenants'] = self.generate_tenant_report(start_date, end_date)
        
        return report
    
    def generate_system_report(self, start_date, end_date):
        """Generate system metrics report"""
        report = {'metrics': {}}
        
        # Get system metrics by category
        categories = SystemMetric.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).values_list('category', flat=True).distinct()
        
        for category in categories:
            metrics = SystemMetric.objects.filter(
                category=category,
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            
            # Group by metric name
            metric_names = metrics.values_list('name', flat=True).distinct()
            category_data = {}
            
            for name in metric_names:
                name_metrics = metrics.filter(name=name)
                
                # Calculate statistics
                stats = name_metrics.aggregate(
                    avg=Avg('value'),
                    max=Max('value'),
                    min=Min('value'),
                    count=Count('id')
                )
                
                # Get latest value
                latest = name_metrics.order_by('-created_at').first()
                
                category_data[name] = {
                    'average': stats['avg'],
                    'maximum': stats['max'],
                    'minimum': stats['min'],
                    'samples': stats['count'],
                    'latest': latest.value if latest else None,
                    'unit': latest.unit if latest else '',
                    'trend': self.calculate_trend(name_metrics)
                }
            
            report['metrics'][category] = category_data
        
        # Add alert summary
        alerts = Alert.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
            alert_type='system'
        )
        
        report['alerts'] = {
            'total': alerts.count(),
            'critical': alerts.filter(level='critical').count(),
            'warning': alerts.filter(level='warning').count(),
            'info': alerts.filter(level='info').count(),
            'resolved': alerts.filter(resolved=True).count(),
            'unresolved': alerts.filter(resolved=False).count()
        }
        
        return report
    
    def generate_tenant_report(self, start_date, end_date, tenant_id=None):
        """Generate tenant metrics report"""
        if tenant_id:
            # Single tenant report
            try:
                tenant = Tenant.objects.get(id=tenant_id)
                return self.generate_single_tenant_report(tenant, start_date, end_date)
            except Tenant.DoesNotExist:
                raise CommandError(f"Tenant with ID {tenant_id} not found")
        else:
            # All tenants summary report
            tenants_report = {}
            
            for tenant in Tenant.objects.all():
                tenants_report[str(tenant.id)] = {
                    'name': tenant.name,
                    'metrics': self.generate_single_tenant_report(tenant, start_date, end_date)
                }
            
            return tenants_report
    
    def generate_single_tenant_report(self, tenant, start_date, end_date):
        """Generate report for a single tenant"""
        report = {'metrics': {}}
        
        # Get tenant metrics by category
        categories = TenantMetric.objects.filter(
            tenant=tenant,
            created_at__gte=start_date,
            created_at__lte=end_date
        ).values_list('category', flat=True).distinct()
        
        for category in categories:
            metrics = TenantMetric.objects.filter(
                tenant=tenant,
                category=category,
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            
            # Group by metric name
            metric_names = metrics.values_list('name', flat=True).distinct()
            category_data = {}
            
            for name in metric_names:
                name_metrics = metrics.filter(name=name)
                
                # Calculate statistics
                stats = name_metrics.aggregate(
                    avg=Avg('value'),
                    max=Max('value'),
                    min=Min('value'),
                    count=Count('id')
                )
                
                # Get latest value
                latest = name_metrics.order_by('-created_at').first()
                
                category_data[name] = {
                    'average': stats['avg'],
                    'maximum': stats['max'],
                    'minimum': stats['min'],
                    'samples': stats['count'],
                    'latest': latest.value if latest else None,
                    'unit': latest.unit if latest else '',
                    'trend': self.calculate_trend(name_metrics)
                }
            
            report['metrics'][category] = category_data
        
        # Add alert summary
        alerts = Alert.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
            tenant=tenant
        )
        
        report['alerts'] = {
            'total': alerts.count(),
            'critical': alerts.filter(level='critical').count(),
            'warning': alerts.filter(level='warning').count(),
            'info': alerts.filter(level='info').count(),
            'resolved': alerts.filter(resolved=True).count(),
            'unresolved': alerts.filter(resolved=False).count()
        }
        
        return report
    
    def generate_performance_report(self, start_date, end_date, tenant_id=None):
        """Generate performance metrics report"""
        report = {}
        
        # Filter performance logs
        logs_query = PerformanceLog.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id)
                logs_query = logs_query.filter(tenant=tenant)
                report['tenant'] = tenant.name
            except Tenant.DoesNotExist:
                raise CommandError(f"Tenant with ID {tenant_id} not found")
        
        # Overall statistics
        overall_stats = logs_query.aggregate(
            avg_duration=Avg('duration_ms'),
            max_duration=Max('duration_ms'),
            min_duration=Min('duration_ms'),
            total_operations=Count('id'),
            success_count=Count('id', filter=models.Q(status='success')),
            error_count=Count('id', filter=models.Q(status='error'))
        )
        
        report['overall'] = {
            'average_duration_ms': overall_stats['avg_duration'],
            'max_duration_ms': overall_stats['max_duration'],
            'min_duration_ms': overall_stats['min_duration'],
            'total_operations': overall_stats['total_operations'],
            'success_rate': (overall_stats['success_count'] / overall_stats['total_operations'] * 100) 
                if overall_stats['total_operations'] > 0 else 0,
            'error_rate': (overall_stats['error_count'] / overall_stats['total_operations'] * 100) 
                if overall_stats['total_operations'] > 0 else 0
        }
        
        # Group by operation type
        operation_types = logs_query.values_list('operation_type', flat=True).distinct()
        report['by_operation'] = {}
        
        for op_type in operation_types:
            op_logs = logs_query.filter(operation_type=op_type)
            op_stats = op_logs.aggregate(
                avg_duration=Avg('duration_ms'),
                max_duration=Max('duration_ms'),
                count=Count('id'),
                error_count=Count('id', filter=models.Q(status='error'))
            )
            
            report['by_operation'][op_type] = {
                'average_duration_ms': op_stats['avg_duration'],
                'max_duration_ms': op_stats['max_duration'],
                'count': op_stats['count'],
                'error_rate': (op_stats['error_count'] / op_stats['count'] * 100) if op_stats['count'] > 0 else 0
            }
        
        # Time-based analysis (daily averages)
        daily_stats = {}
        current_date = start_date.date()
        end_date_day = end_date.date()
        
        while current_date <= end_date_day:
            day_logs = logs_query.filter(
                created_at__date=current_date
            )
            
            if day_logs.exists():
                day_stats = day_logs.aggregate(
                    avg_duration=Avg('duration_ms'),
                    count=Count('id')
                )
                
                daily_stats[current_date.isoformat()] = {
                    'average_duration_ms': day_stats['avg_duration'],
                    'operation_count': day_stats['count']
                }
            
            current_date += timedelta(days=1)
        
        report['daily_trends'] = daily_stats
        
        return report
    
    def generate_health_report(self, start_date, end_date):
        """Generate health check report"""
        report = {}
        
        # Get health check results
        health_checks = HealthCheckResult.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Overall health status
        latest_system_check = health_checks.filter(check_type='system').order_by('-created_at').first()
        report['current_status'] = latest_system_check.status if latest_system_check else 'unknown'
        
        # Health check types
        check_types = health_checks.values_list('check_type', flat=True).distinct()
        report['components'] = {}
        
        for check_type in check_types:
            type_checks = health_checks.filter(check_type=check_type)
            latest = type_checks.order_by('-created_at').first()
            
            # Calculate uptime percentage
            healthy_count = type_checks.filter(status='healthy').count()
            total_count = type_checks.count()
            uptime_pct = (healthy_count / total_count * 100) if total_count > 0 else 0
            
            report['components'][check_type] = {
                'current_status': latest.status if latest else 'unknown',
                'last_checked': latest.created_at.isoformat() if latest else None,
                'uptime_percentage': uptime_pct,
                'checks_performed': total_count,
                'status_counts': {
                    'healthy': type_checks.filter(status='healthy').count(),
                    'warning': type_checks.filter(status='warning').count(),
                    'unhealthy': type_checks.filter(status='unhealthy').count(),
                    'skipped': type_checks.filter(status='skipped').count()
                }
            }
        
        # Calculate overall uptime
        system_checks = health_checks.filter(check_type='system')
        healthy_system_checks = system_checks.filter(status='healthy').count()
        total_system_checks = system_checks.count()
        
        report['overall_uptime'] = (healthy_system_checks / total_system_checks * 100) if total_system_checks > 0 else 0
        
        return report
    
    def calculate_trend(self, metrics_queryset):
        """Calculate trend direction based on metric values"""
        if not metrics_queryset.exists() or metrics_queryset.count() < 2:
            return 'stable'
        
        # Get oldest and newest values
        oldest = metrics_queryset.order_by('created_at').first()
        newest = metrics_queryset.order_by('-created_at').first()
        
        # Calculate percentage change
        if oldest.value == 0:
            return 'increasing' if newest.value > 0 else 'stable'
        
        change_pct = ((newest.value - oldest.value) / abs(oldest.value)) * 100
        
        if abs(change_pct) < 5:  # Less than 5% change is considered stable
            return 'stable'
        elif change_pct > 0:
            return 'increasing'
        else:
            return 'decreasing'
    
    def output_to_file(self, data, file_path, output_format):
        """Output report to a file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            if output_format == 'json':
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
            elif output_format == 'csv':
                self.output_csv(data, file_path)
            else:  # text format
                with open(file_path, 'w') as f:
                    f.write(self.format_text_report(data))
            
            self.stdout.write(self.style.SUCCESS(f"Report saved to {file_path}"))
        except Exception as e:
            raise CommandError(f"Failed to write to file: {e}")
    
    def output_to_stdout(self, data, output_format):
        """Output report to stdout"""
        if output_format == 'json':
            self.stdout.write(json.dumps(data, indent=2))
        else:  # text format
            self.stdout.write(self.format_text_report(data))
    
    def output_csv(self, data, file_path):
        """Output report in CSV format"""
        # This is a simplified implementation that flattens the data structure
        # A more complete implementation would handle nested structures better
        
        # Create a flattened version of the data
        flattened_data = self.flatten_dict(data)
        
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Key', 'Value'])  # Header row
            
            for key, value in flattened_data.items():
                writer.writerow([key, value])
    
    def flatten_dict(self, d, parent_key='', sep='.'):
        """Flatten a nested dictionary"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def format_text_report(self, data):
        """Format report as readable text"""
        lines = []
        
        # Add metadata
        if 'metadata' in data:
            lines.append("REPORT METADATA")
            lines.append("===============")
            for key, value in data['metadata'].items():
                lines.append(f"{key}: {value}")
            lines.append("")
        
        # Format system report
        if 'system' in data:
            lines.append("SYSTEM METRICS")
            lines.append("===============")
            self._format_metrics_section(data['system'], lines)
            lines.append("")
        
        # Format health report
        if 'health' in data:
            lines.append("HEALTH STATUS")
            lines.append("==============")
            health = data['health']
            lines.append(f"Current Status: {health.get('current_status', 'unknown').upper()}")
            lines.append(f"Overall Uptime: {health.get('overall_uptime', 0):.2f}%")
            
            if 'components' in health:
                lines.append("\nComponent Status:")
                for comp, status in health['components'].items():
                    lines.append(f"  {comp}: {status.get('current_status', 'unknown').upper()} ")
                    lines.append(f"    Uptime: {status.get('uptime_percentage', 0):.2f}%")
            lines.append("")
        
        # Format performance report
        if 'performance' in data:
            lines.append("PERFORMANCE METRICS")
            lines.append("===================")
            perf = data['performance']
            if 'overall' in perf:
                overall = perf['overall']
                lines.append(f"Average Response Time: {overall.get('average_duration_ms', 0):.2f} ms")
                lines.append(f"Maximum Response Time: {overall.get('max_duration_ms', 0):.2f} ms")
                lines.append(f"Success Rate: {overall.get('success_rate', 0):.2f}%")
                lines.append(f"Total Operations: {overall.get('total_operations', 0)}")
            lines.append("")
        
        # Format tenant report(s)
        if 'tenant' in data:
            lines.append(f"TENANT METRICS: {data.get('tenant', '')}")
            lines.append("===============")
            self._format_metrics_section(data['tenant'], lines)
        elif 'tenants' in data:
            lines.append("TENANTS SUMMARY")
            lines.append("===============")
            for tenant_id, tenant_data in data['tenants'].items():
                lines.append(f"\nTenant: {tenant_data.get('name', tenant_id)}")
                lines.append("-" * (len(tenant_data.get('name', tenant_id)) + 8))
                self._format_metrics_section(tenant_data.get('metrics', {}), lines, indent=2)
        
        return "\n".join(lines)
    
    def _format_metrics_section(self, metrics_data, lines, indent=0):
        """Helper to format metrics sections in text report"""
        indent_str = " " * indent
        
        if 'metrics' in metrics_data:
            for category, category_data in metrics_data['metrics'].items():
                lines.append(f"{indent_str}{category.upper()}:")
                for name, values in category_data.items():
                    latest = values.get('latest')
                    unit = values.get('unit', '')
                    avg = values.get('average')
                    trend = values.get('trend', 'stable')
                    
                    trend_indicator = '↑' if trend == 'increasing' else '↓' if trend == 'decreasing' else '→'
                    
                    lines.append(f"{indent_str}  {name}: {latest} {unit} {trend_indicator} (avg: {avg:.2f} {unit})")
        
        if 'alerts' in metrics_data:
            alerts = metrics_data['alerts']
            lines.append(f"{indent_str}Alerts:")
            lines.append(f"{indent_str}  Total: {alerts.get('total', 0)}")
            lines.append(f"{indent_str}  Critical: {alerts.get('critical', 0)}")
            lines.append(f"{indent_str}  Warning: {alerts.get('warning', 0)}")
            lines.append(f"{indent_str}  Unresolved: {alerts.get('unresolved', 0)}")