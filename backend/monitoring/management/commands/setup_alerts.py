import os
import json
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.conf import settings
from django.db.models import Count

from monitoring.models import Alert, SystemMetric, TenantMetric


class Command(BaseCommand):
    help = 'Set up monitoring alert thresholds and configurations'
    
    # Default thresholds for system metrics
    DEFAULT_SYSTEM_THRESHOLDS = {
        'cpu': {
            'percent': {'warning': 80, 'critical': 90, 'unit': '%'},
            'load_1': {'warning': 4, 'critical': 8, 'unit': ''},
            'load_5': {'warning': 3, 'critical': 6, 'unit': ''},
            'load_15': {'warning': 2, 'critical': 4, 'unit': ''}
        },
        'memory': {
            'percent': {'warning': 85, 'critical': 95, 'unit': '%'},
            'swap_percent': {'warning': 60, 'critical': 80, 'unit': '%'}
        },
        'disk': {
            'percent': {'warning': 85, 'critical': 95, 'unit': '%'}
        },
        'database': {
            'connections': {'warning': 80, 'critical': 95, 'unit': '%'},
            'slow_queries': {'warning': 10, 'critical': 20, 'unit': 'count'}
        },
        'redis': {
            'memory_percent': {'warning': 70, 'critical': 85, 'unit': '%'},
            'connected_clients': {'warning': 80, 'critical': 95, 'unit': '%'}
        }
    }
    
    # Default thresholds for tenant metrics
    DEFAULT_TENANT_THRESHOLDS = {
        'users': {
            'total': {'warning': 80, 'critical': 95, 'unit': '%'}
        },
        'storage': {
            'used_percent': {'warning': 80, 'critical': 90, 'unit': '%'}
        },
        'api_usage': {
            'daily_avg': {'warning': 80, 'critical': 95, 'unit': '%'},
            'percent_used': {'warning': 80, 'critical': 95, 'unit': '%'}
        },
        'performance': {
            'avg_duration': {'warning': 1000, 'critical': 3000, 'unit': 'ms'},
            'error_rate': {'warning': 5, 'critical': 10, 'unit': '%'}
        }
    }
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            dest='reset',
            default=False,
            help='Reset all thresholds to default values',
        )
        parser.add_argument(
            '--import',
            dest='import_file',
            type=str,
            help='Import thresholds from JSON file',
        )
        parser.add_argument(
            '--export',
            dest='export_file',
            type=str,
            help='Export current thresholds to JSON file',
        )
        parser.add_argument(
            '--apply',
            action='store_true',
            dest='apply',
            default=False,
            help='Apply thresholds and check for new alerts',
        )
    
    def handle(self, *args, **options):
        reset = options['reset']
        import_file = options.get('import_file')
        export_file = options.get('export_file')
        apply = options['apply']
        
        # Get current thresholds from settings or use defaults
        current_system_thresholds = getattr(settings, 'SYSTEM_METRIC_THRESHOLDS', self.DEFAULT_SYSTEM_THRESHOLDS)
        current_tenant_thresholds = getattr(settings, 'TENANT_METRIC_THRESHOLDS', self.DEFAULT_TENANT_THRESHOLDS)
        
        # Reset thresholds if requested
        if reset:
            self.stdout.write(self.style.WARNING('Resetting all thresholds to default values'))
            current_system_thresholds = self.DEFAULT_SYSTEM_THRESHOLDS
            current_tenant_thresholds = self.DEFAULT_TENANT_THRESHOLDS
        
        # Import thresholds from file if specified
        if import_file:
            try:
                self.stdout.write(f"Importing thresholds from {import_file}")
                with open(import_file, 'r') as f:
                    imported_thresholds = json.load(f)
                
                if 'system' in imported_thresholds:
                    current_system_thresholds = imported_thresholds['system']
                if 'tenant' in imported_thresholds:
                    current_tenant_thresholds = imported_thresholds['tenant']
                    
                self.stdout.write(self.style.SUCCESS(f"Successfully imported thresholds from {import_file}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error importing thresholds: {e}"))
                raise CommandError(f"Import failed: {e}")
        
        # Export thresholds to file if specified
        if export_file:
            try:
                self.stdout.write(f"Exporting thresholds to {export_file}")
                export_data = {
                    'system': current_system_thresholds,
                    'tenant': current_tenant_thresholds,
                    'exported_at': timezone.now().isoformat()
                }
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(os.path.abspath(export_file)), exist_ok=True)
                
                with open(export_file, 'w') as f:
                    json.dump(export_data, f, indent=2)
                    
                self.stdout.write(self.style.SUCCESS(f"Successfully exported thresholds to {export_file}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error exporting thresholds: {e}"))
                raise CommandError(f"Export failed: {e}")
        
        # Display current thresholds
        self.stdout.write(self.style.SUCCESS('Current System Metric Thresholds:'))
        self._display_thresholds(current_system_thresholds)
        
        self.stdout.write(self.style.SUCCESS('\nCurrent Tenant Metric Thresholds:'))
        self._display_thresholds(current_tenant_thresholds)
        
        # Apply thresholds and check for alerts if requested
        if apply:
            self.stdout.write(self.style.WARNING('\nApplying thresholds and checking for new alerts...'))
            system_alerts = self._check_system_alerts(current_system_thresholds)
            tenant_alerts = self._check_tenant_alerts(current_tenant_thresholds)
            
            total_alerts = system_alerts + tenant_alerts
            self.stdout.write(self.style.SUCCESS(f"Created {total_alerts} new alerts ({system_alerts} system, {tenant_alerts} tenant)"))
    
    def _display_thresholds(self, thresholds, indent=0):
        """Display thresholds in a readable format"""
        indent_str = ' ' * indent
        for category, metrics in thresholds.items():
            self.stdout.write(f"{indent_str}{category}:")
            for metric, levels in metrics.items():
                self.stdout.write(f"{indent_str}  {metric}:")
                for level, value in levels.items():
                    if level in ['warning', 'critical']:
                        self.stdout.write(f"{indent_str}    {level}: {value} {levels.get('unit', '')}")
    
    def _check_system_alerts(self, thresholds):
        """Check system metrics against thresholds and create alerts"""
        alert_count = 0
        
        # Get latest system metrics
        latest_metrics = {}
        for metric in SystemMetric.objects.all().order_by('category', 'name', '-created_at').distinct('category', 'name'):
            key = f"{metric.category}_{metric.name}"
            if key not in latest_metrics:
                latest_metrics[key] = metric
        
        # Check each metric against thresholds
        for key, metric in latest_metrics.items():
            category = metric.category
            name = metric.name
            
            if category in thresholds and name in thresholds[category]:
                threshold = thresholds[category][name]
                
                # Skip non-numeric values
                try:
                    value = float(metric.value)
                except (ValueError, TypeError):
                    continue
                
                # Check critical threshold first
                if 'critical' in threshold and value >= threshold['critical']:
                    alert = self._create_alert(
                        level='critical',
                        message=f"System {category} {name} is critical: {value} {metric.unit}",
                        metric_type='system',
                        metric_id=metric.id,
                        category=category,
                        name=name,
                        value=value,
                        threshold=threshold['critical']
                    )
                    if alert:
                        alert_count += 1
                # Then check warning threshold
                elif 'warning' in threshold and value >= threshold['warning']:
                    alert = self._create_alert(
                        level='warning',
                        message=f"System {category} {name} is high: {value} {metric.unit}",
                        metric_type='system',
                        metric_id=metric.id,
                        category=category,
                        name=name,
                        value=value,
                        threshold=threshold['warning']
                    )
                    if alert:
                        alert_count += 1
        
        return alert_count
    
    def _check_tenant_alerts(self, thresholds):
        """Check tenant metrics against thresholds and create alerts"""
        alert_count = 0
        
        # Get latest tenant metrics
        latest_metrics = {}
        for metric in TenantMetric.objects.all().order_by('tenant', 'category', 'name', '-created_at').distinct('tenant', 'category', 'name'):
            key = f"{metric.tenant.id}_{metric.category}_{metric.name}"
            if key not in latest_metrics:
                latest_metrics[key] = metric
        
        # Check each metric against thresholds
        for key, metric in latest_metrics.items():
            category = metric.category
            name = metric.name
            tenant = metric.tenant
            
            if category in thresholds and name in thresholds[category]:
                threshold = thresholds[category][name]
                
                # Skip non-numeric values
                try:
                    value = float(metric.value)
                except (ValueError, TypeError):
                    continue
                
                # Check critical threshold first
                if 'critical' in threshold and value >= threshold['critical']:
                    alert = self._create_alert(
                        level='critical',
                        message=f"Tenant {tenant.name} {category} {name} is critical: {value} {metric.unit}",
                        metric_type='tenant',
                        metric_id=metric.id,
                        category=category,
                        name=name,
                        value=value,
                        threshold=threshold['critical'],
                        tenant=tenant
                    )
                    if alert:
                        alert_count += 1
                # Then check warning threshold
                elif 'warning' in threshold and value >= threshold['warning']:
                    alert = self._create_alert(
                        level='warning',
                        message=f"Tenant {tenant.name} {category} {name} is high: {value} {metric.unit}",
                        metric_type='tenant',
                        metric_id=metric.id,
                        category=category,
                        name=name,
                        value=value,
                        threshold=threshold['warning'],
                        tenant=tenant
                    )
                    if alert:
                        alert_count += 1
        
        return alert_count
    
    def _create_alert(self, level, message, metric_type, metric_id, category, name, value, threshold, tenant=None):
        """Create a new alert if one doesn't already exist for this metric"""
        # Check if there's already an unresolved alert for this metric
        existing_filters = {
            'alert_type': metric_type,
            'category': category,
            'name': name,
            'resolved': False
        }
        
        if tenant:
            existing_filters['tenant'] = tenant
        
        existing_alert = Alert.objects.filter(**existing_filters).first()
        
        if existing_alert:
            # Update existing alert if level changed
            if existing_alert.level != level:
                existing_alert.level = level
                existing_alert.message = message
                existing_alert.value = value
                existing_alert.threshold = threshold
                existing_alert.save()
                self.stdout.write(f"Updated alert: {message}")
                return existing_alert
            return None
        else:
            # Create new alert
            alert_data = {
                'level': level,
                'message': message,
                'alert_type': metric_type,
                'category': category,
                'name': name,
                'value': value,
                'threshold': threshold,
                'resolved': False
            }
            
            if tenant:
                alert_data['tenant'] = tenant
            
            alert = Alert.objects.create(**alert_data)
            self.stdout.write(f"New alert: {message}")
            return alert