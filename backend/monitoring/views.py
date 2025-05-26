from django.utils import timezone
from django.db.models import Avg, Min, Max, Count
from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsSuperUser, IsSuperUserOrTenantAdmin
from .models import SystemMetric, TenantMetric, PerformanceLog, Alert, HealthCheckResult
from .serializers import (
    SystemMetricSerializer, TenantMetricSerializer, PerformanceLogSerializer,
    AlertSerializer, AlertResolveSerializer, HealthCheckResultSerializer,
    SystemHealthSerializer, MetricAggregationSerializer
)
import logging
import psutil
import redis
import json
from django.conf import settings
from django.db import connection
from django_redis import get_redis_connection
from datetime import timedelta

logger = logging.getLogger(__name__)


class SystemMetricViewSet(viewsets.ModelViewSet):
    """API endpoint for system metrics"""
    queryset = SystemMetric.objects.all()
    serializer_class = SystemMetricSerializer
    permission_classes = [IsSuperUser]
    filterset_fields = ['name', 'category']
    search_fields = ['name']
    ordering_fields = ['name', 'value', 'timestamp', 'category']
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get all available metric categories"""
        categories = dict(SystemMetric._meta.get_field('category').choices)
        return Response(categories)
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current system metrics"""
        # Collect current system metrics
        metrics = self._collect_system_metrics()
        
        # Save metrics to database
        for name, data in metrics.items():
            SystemMetric.objects.create(
                name=name,
                value=data['value'],
                unit=data['unit'],
                category=data['category']
            )
        
        return Response(metrics)
    
    @action(detail=False, methods=['get'])
    def aggregate(self, request):
        """Get aggregated metrics for a specific time period"""
        metric_name = request.query_params.get('name')
        category = request.query_params.get('category')
        days = int(request.query_params.get('days', 7))
        
        if not metric_name and not category:
            return Response(
                {"error": _("Either metric name or category is required")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate time range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Filter metrics
        queryset = SystemMetric.objects.filter(timestamp__range=(start_date, end_date))
        if metric_name:
            queryset = queryset.filter(name=metric_name)
        if category:
            queryset = queryset.filter(category=category)
        
        # Group by name and calculate aggregates
        result = []
        for name in queryset.values_list('name', flat=True).distinct():
            name_metrics = queryset.filter(name=name).order_by('timestamp')
            if not name_metrics.exists():
                continue
                
            # Get unit and category from the latest record
            latest = name_metrics.latest('timestamp')
            unit = latest.unit
            
            # Calculate aggregates
            aggregates = name_metrics.aggregate(
                avg=Avg('value'),
                min=Min('value'),
                max=Max('value')
            )
            
            # Calculate trend (percentage change)
            first = name_metrics.earliest('timestamp').value
            last = latest.value
            trend = ((last - first) / first * 100) if first != 0 else 0
            
            # Create data points for chart
            data_points = [{
                'timestamp': m.timestamp,
                'value': m.value
            } for m in name_metrics]
            
            result.append({
                'name': name,
                'avg': aggregates['avg'],
                'min': aggregates['min'],
                'max': aggregates['max'],
                'current': latest.value,
                'unit': unit,
                'trend': trend,
                'data_points': data_points
            })
        
        serializer = MetricAggregationSerializer(result, many=True)
        return Response(serializer.data)
    
    def _collect_system_metrics(self):
        """Collect current system metrics"""
        metrics = {}
        
        # CPU metrics
        metrics['cpu_percent'] = {
            'value': psutil.cpu_percent(interval=1),
            'unit': '%',
            'category': 'cpu'
        }
        
        # Memory metrics
        memory = psutil.virtual_memory()
        metrics['memory_percent'] = {
            'value': memory.percent,
            'unit': '%',
            'category': 'memory'
        }
        metrics['memory_available'] = {
            'value': memory.available / (1024 * 1024 * 1024),  # Convert to GB
            'unit': 'GB',
            'category': 'memory'
        }
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        metrics['disk_percent'] = {
            'value': disk.percent,
            'unit': '%',
            'category': 'disk'
        }
        metrics['disk_free'] = {
            'value': disk.free / (1024 * 1024 * 1024),  # Convert to GB
            'unit': 'GB',
            'category': 'disk'
        }
        
        # Network metrics
        net_io = psutil.net_io_counters()
        metrics['network_sent'] = {
            'value': net_io.bytes_sent / (1024 * 1024),  # Convert to MB
            'unit': 'MB',
            'category': 'network'
        }
        metrics['network_received'] = {
            'value': net_io.bytes_recv / (1024 * 1024),  # Convert to MB
            'unit': 'MB',
            'category': 'network'
        }
        
        # Database metrics
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM pg_stat_activity")
                db_connections = cursor.fetchone()[0]
                metrics['db_connections'] = {
                    'value': db_connections,
                    'unit': 'connections',
                    'category': 'database'
                }
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")
        
        # Redis metrics
        try:
            redis_client = get_redis_connection("default")
            redis_info = redis_client.info()
            metrics['redis_memory'] = {
                'value': redis_info['used_memory'] / (1024 * 1024),  # Convert to MB
                'unit': 'MB',
                'category': 'application'
            }
            metrics['redis_clients'] = {
                'value': redis_info['connected_clients'],
                'unit': 'clients',
                'category': 'application'
            }
        except Exception as e:
            logger.error(f"Error collecting Redis metrics: {e}")
        
        return metrics


class TenantMetricViewSet(viewsets.ModelViewSet):
    """API endpoint for tenant-specific metrics"""
    serializer_class = TenantMetricSerializer
    permission_classes = [IsSuperUserOrTenantAdmin]
    filterset_fields = ['tenant', 'name', 'category']
    search_fields = ['name', 'tenant__name']
    ordering_fields = ['name', 'value', 'timestamp', 'category', 'tenant__name']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return TenantMetric.objects.all()
        return TenantMetric.objects.filter(tenant=user.tenant)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get all available metric categories"""
        categories = dict(TenantMetric._meta.get_field('category').choices)
        return Response(categories)
    
    @action(detail=False, methods=['get'])
    def aggregate(self, request):
        """Get aggregated metrics for a specific time period"""
        metric_name = request.query_params.get('name')
        category = request.query_params.get('category')
        days = int(request.query_params.get('days', 7))
        tenant_id = request.query_params.get('tenant')
        
        if not metric_name and not category:
            return Response(
                {"error": _("Either metric name or category is required")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate time range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Filter metrics
        queryset = self.get_queryset().filter(timestamp__range=(start_date, end_date))
        if metric_name:
            queryset = queryset.filter(name=metric_name)
        if category:
            queryset = queryset.filter(category=category)
        if tenant_id and self.request.user.is_superuser:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        # Group by name and calculate aggregates
        result = []
        for name in queryset.values_list('name', flat=True).distinct():
            name_metrics = queryset.filter(name=name).order_by('timestamp')
            if not name_metrics.exists():
                continue
                
            # Get unit from the latest record
            latest = name_metrics.latest('timestamp')
            unit = latest.unit
            
            # Calculate aggregates
            aggregates = name_metrics.aggregate(
                avg=Avg('value'),
                min=Min('value'),
                max=Max('value')
            )
            
            # Calculate trend (percentage change)
            first = name_metrics.earliest('timestamp').value
            last = latest.value
            trend = ((last - first) / first * 100) if first != 0 else 0
            
            # Create data points for chart
            data_points = [{
                'timestamp': m.timestamp,
                'value': m.value
            } for m in name_metrics]
            
            result.append({
                'name': name,
                'avg': aggregates['avg'],
                'min': aggregates['min'],
                'max': aggregates['max'],
                'current': latest.value,
                'unit': unit,
                'trend': trend,
                'data_points': data_points
            })
        
        serializer = MetricAggregationSerializer(result, many=True)
        return Response(serializer.data)


class PerformanceLogViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for performance logs"""
    serializer_class = PerformanceLogSerializer
    permission_classes = [IsSuperUserOrTenantAdmin]
    filterset_fields = ['tenant', 'user', 'operation', 'status', 'resource_type']
    search_fields = ['operation', 'resource_type', 'resource_id']
    ordering_fields = ['operation', 'duration_ms', 'status', 'timestamp']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return PerformanceLog.objects.all()
        return PerformanceLog.objects.filter(tenant=user.tenant)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get performance statistics"""
        days = int(request.query_params.get('days', 7))
        operation = request.query_params.get('operation')
        
        # Calculate time range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Filter logs
        queryset = self.get_queryset().filter(timestamp__range=(start_date, end_date))
        if operation:
            queryset = queryset.filter(operation=operation)
        
        # Calculate statistics
        stats = queryset.aggregate(
            avg_duration=Avg('duration_ms'),
            min_duration=Min('duration_ms'),
            max_duration=Max('duration_ms'),
            total_operations=Count('id'),
            success_count=Count('id', filter=models.Q(status='success')),
            error_count=Count('id', filter=models.Q(status='error')),
            timeout_count=Count('id', filter=models.Q(status='timeout'))
        )
        
        # Calculate success rate
        total = stats['total_operations']
        stats['success_rate'] = (stats['success_count'] / total * 100) if total > 0 else 0
        
        # Get top 5 slowest operations
        slowest = queryset.order_by('-duration_ms')[:5]
        stats['slowest_operations'] = PerformanceLogSerializer(slowest, many=True).data
        
        # Get operations by type
        operations_by_type = queryset.values('operation').annotate(
            count=Count('id'),
            avg_duration=Avg('duration_ms')
        ).order_by('-count')
        stats['operations_by_type'] = list(operations_by_type)
        
        return Response(stats)


class AlertViewSet(viewsets.ModelViewSet):
    """API endpoint for system and tenant alerts"""
    serializer_class = AlertSerializer
    permission_classes = [IsSuperUserOrTenantAdmin]
    filterset_fields = ['tenant', 'level', 'category', 'is_active']
    search_fields = ['title', 'message']
    ordering_fields = ['created_at', 'level', 'category', 'is_active']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Alert.objects.all()
        return Alert.objects.filter(tenant=user.tenant)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark an alert as resolved"""
        alert = self.get_object()
        serializer = AlertResolveSerializer(data=request.data)
        
        if serializer.is_valid():
            notes = serializer.validated_data.get('resolution_notes', '')
            alert.resolve(user=request.user, notes=notes)
            return Response(AlertSerializer(alert).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get alert summary statistics"""
        queryset = self.get_queryset()
        
        # Count alerts by level
        level_counts = queryset.values('level').annotate(count=Count('id'))
        level_summary = {item['level']: item['count'] for item in level_counts}
        
        # Count active vs resolved
        active_count = queryset.filter(is_active=True).count()
        resolved_count = queryset.filter(is_active=False).count()
        
        # Count by category
        category_counts = queryset.values('category').annotate(count=Count('id'))
        category_summary = {item['category']: item['count'] for item in category_counts}
        
        # Recent alerts
        recent_alerts = queryset.order_by('-created_at')[:5]
        
        return Response({
            'total_alerts': active_count + resolved_count,
            'active_alerts': active_count,
            'resolved_alerts': resolved_count,
            'by_level': level_summary,
            'by_category': category_summary,
            'recent_alerts': AlertSerializer(recent_alerts, many=True).data
        })


class HealthCheckResultViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for health check results"""
    queryset = HealthCheckResult.objects.all()
    serializer_class = HealthCheckResultSerializer
    permission_classes = [IsSuperUser]
    filterset_fields = ['check_name', 'status']
    search_fields = ['check_name', 'message']
    ordering_fields = ['check_name', 'status', 'timestamp']


class SystemHealthView(views.APIView):
    """API endpoint for overall system health"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current system health status"""
        # Perform health checks
        health_status = self._check_system_health()
        
        # Save health check results
        for check_name, check_data in health_status['checks'].items():
            HealthCheckResult.objects.create(
                check_name=check_name,
                status=check_data['status'],
                message=check_data.get('message', ''),
                details=check_data.get('details', {})
            )
        
        serializer = SystemHealthSerializer(health_status)
        return Response(serializer.data)
    
    def _check_system_health(self):
        """Perform system health checks"""
        checks = {}
        overall_status = 'ok'
        metrics = {}
        
        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                checks['database'] = {
                    'status': 'ok',
                    'message': _('Database connection successful')
                }
        except Exception as e:
            checks['database'] = {
                'status': 'error',
                'message': _('Database connection failed'),
                'details': {'error': str(e)}
            }
            overall_status = 'error'
        
        # Check Redis connection
        try:
            redis_client = get_redis_connection("default")
            redis_client.ping()
            checks['redis'] = {
                'status': 'ok',
                'message': _('Redis connection successful')
            }
        except Exception as e:
            checks['redis'] = {
                'status': 'error',
                'message': _('Redis connection failed'),
                'details': {'error': str(e)}
            }
            overall_status = 'error'
        
        # Check disk space
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        metrics['disk_usage'] = disk_percent
        if disk_percent > 90:
            checks['disk'] = {
                'status': 'error',
                'message': _('Disk usage critical'),
                'details': {'percent': disk_percent, 'free_gb': disk.free / (1024**3)}
            }
            overall_status = 'error'
        elif disk_percent > 80:
            checks['disk'] = {
                'status': 'warning',
                'message': _('Disk usage high'),
                'details': {'percent': disk_percent, 'free_gb': disk.free / (1024**3)}
            }
            if overall_status == 'ok':
                overall_status = 'warning'
        else:
            checks['disk'] = {
                'status': 'ok',
                'message': _('Disk usage normal'),
                'details': {'percent': disk_percent, 'free_gb': disk.free / (1024**3)}
            }
        
        # Check memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        metrics['memory_usage'] = memory_percent
        if memory_percent > 90:
            checks['memory'] = {
                'status': 'error',
                'message': _('Memory usage critical'),
                'details': {'percent': memory_percent, 'available_gb': memory.available / (1024**3)}
            }
            overall_status = 'error'
        elif memory_percent > 80:
            checks['memory'] = {
                'status': 'warning',
                'message': _('Memory usage high'),
                'details': {'percent': memory_percent, 'available_gb': memory.available / (1024**3)}
            }
            if overall_status == 'ok':
                overall_status = 'warning'
        else:
            checks['memory'] = {
                'status': 'ok',
                'message': _('Memory usage normal'),
                'details': {'percent': memory_percent, 'available_gb': memory.available / (1024**3)}
            }
        
        # Check CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        metrics['cpu_usage'] = cpu_percent
        if cpu_percent > 90:
            checks['cpu'] = {
                'status': 'error',
                'message': _('CPU usage critical'),
                'details': {'percent': cpu_percent}
            }
            overall_status = 'error'
        elif cpu_percent > 80:
            checks['cpu'] = {
                'status': 'warning',
                'message': _('CPU usage high'),
                'details': {'percent': cpu_percent}
            }
            if overall_status == 'ok':
                overall_status = 'warning'
        else:
            checks['cpu'] = {
                'status': 'ok',
                'message': _('CPU usage normal'),
                'details': {'percent': cpu_percent}
            }
        
        # Check application version
        version = getattr(settings, 'VERSION', '1.0.0')
        
        return {
            'status': overall_status,
            'version': version,
            'timestamp': timezone.now(),
            'checks': checks,
            'metrics': metrics
        }


class MetricsExportView(views.APIView):
    """API endpoint for exporting metrics in Prometheus format"""
    permission_classes = []
    
    def get(self, request):
        """Export metrics in Prometheus format"""
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        
        # Generate metrics
        metrics_data = generate_latest()
        
        return Response(
            metrics_data,
            content_type=CONTENT_TYPE_LATEST
        )