from rest_framework import serializers
from .models import SystemMetric, TenantMetric, PerformanceLog, Alert, HealthCheckResult
from authentication.serializers import UserSerializer


class SystemMetricSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = SystemMetric
        fields = ['id', 'name', 'value', 'unit', 'timestamp', 'category', 'category_display']
        read_only_fields = ['id', 'timestamp']


class TenantMetricSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    class Meta:
        model = TenantMetric
        fields = ['id', 'tenant', 'tenant_name', 'name', 'value', 'unit', 'timestamp', 'category', 'category_display']
        read_only_fields = ['id', 'timestamp', 'tenant_name']


class PerformanceLogSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True, allow_null=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = PerformanceLog
        fields = [
            'id', 'tenant', 'tenant_name', 'user', 'user_name', 'operation', 'duration_ms', 
            'status', 'status_display', 'resource_type', 'resource_id', 'metadata', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp', 'tenant_name', 'user_name']


class AlertSerializer(serializers.ModelSerializer):
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True, allow_null=True)
    resolved_by_details = UserSerializer(source='resolved_by', read_only=True, allow_null=True)
    
    class Meta:
        model = Alert
        fields = [
            'id', 'tenant', 'tenant_name', 'title', 'message', 'level', 'level_display', 
            'category', 'category_display', 'is_active', 'created_at', 'resolved_at', 
            'resolved_by', 'resolved_by_details', 'resolution_notes', 'metadata'
        ]
        read_only_fields = ['id', 'created_at', 'tenant_name', 'resolved_by_details']


class AlertResolveSerializer(serializers.Serializer):
    resolution_notes = serializers.CharField(required=False, allow_blank=True)


class HealthCheckResultSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = HealthCheckResult
        fields = ['id', 'check_name', 'status', 'status_display', 'message', 'details', 'timestamp']
        read_only_fields = ['id', 'timestamp', 'status_display']


class SystemHealthSerializer(serializers.Serializer):
    """Serializer for overall system health status"""
    status = serializers.CharField()
    version = serializers.CharField()
    timestamp = serializers.DateTimeField()
    checks = serializers.DictField(child=serializers.DictField())
    metrics = serializers.DictField(child=serializers.FloatField())


class MetricAggregationSerializer(serializers.Serializer):
    """Serializer for aggregated metrics data"""
    name = serializers.CharField()
    avg = serializers.FloatField()
    min = serializers.FloatField()
    max = serializers.FloatField()
    current = serializers.FloatField()
    unit = serializers.CharField(allow_blank=True)
    trend = serializers.FloatField()  # Percentage change
    data_points = serializers.ListField(child=serializers.DictField())