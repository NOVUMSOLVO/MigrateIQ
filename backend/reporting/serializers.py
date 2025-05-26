"""
Serializers for reporting models.
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import (
    ReportTemplate, Report, ScheduledReport, ReportShare, ReportMetric
)


class ReportTemplateSerializer(serializers.ModelSerializer):
    """Serializer for ReportTemplate model."""
    
    tenant_name = serializers.ReadOnlyField(source='tenant.name')
    created_by_name = serializers.ReadOnlyField(source='created_by.get_full_name')
    usage_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ReportTemplate
        fields = [
            'id', 'name', 'description', 'report_type', 'data_sources',
            'filters', 'chart_config', 'columns', 'metrics', 'is_public',
            'tenant_name', 'created_by_name', 'usage_count', 'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id', 'tenant_name', 'created_by_name', 'usage_count',
            'created_at', 'updated_at'
        ]
    
    def get_usage_count(self, obj):
        """Get the number of reports generated from this template."""
        return obj.generated_reports.count()


class ReportSerializer(serializers.ModelSerializer):
    """Serializer for Report model."""
    
    tenant_name = serializers.ReadOnlyField(source='tenant.name')
    template_name = serializers.ReadOnlyField(source='template.name')
    generated_by_name = serializers.ReadOnlyField(source='generated_by.get_full_name')
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = [
            'id', 'name', 'description', 'config', 'data', 'period_start',
            'period_end', 'status', 'error_message', 'export_format',
            'file_path', 'file_size', 'file_size_mb', 'tenant_name',
            'template_name', 'generated_by_name', 'created_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'data', 'status', 'error_message', 'file_path',
            'file_size', 'file_size_mb', 'tenant_name', 'template_name',
            'generated_by_name', 'created_at', 'completed_at'
        ]
    
    def get_file_size_mb(self, obj):
        """Get file size in MB."""
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return None


class ScheduledReportSerializer(serializers.ModelSerializer):
    """Serializer for ScheduledReport model."""
    
    tenant_name = serializers.ReadOnlyField(source='tenant.name')
    template_name = serializers.ReadOnlyField(source='template.name')
    created_by_name = serializers.ReadOnlyField(source='created_by.get_full_name')
    next_run_in_hours = serializers.SerializerMethodField()
    
    class Meta:
        model = ScheduledReport
        fields = [
            'id', 'name', 'description', 'schedule_type', 'cron_expression',
            'recipients', 'export_formats', 'is_active', 'last_run',
            'next_run', 'run_count', 'tenant_name', 'template_name',
            'created_by_name', 'next_run_in_hours', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'last_run', 'next_run', 'run_count', 'tenant_name',
            'template_name', 'created_by_name', 'next_run_in_hours',
            'created_at', 'updated_at'
        ]
    
    def get_next_run_in_hours(self, obj):
        """Get hours until next run."""
        if not obj.next_run:
            return None
        
        from django.utils import timezone
        now = timezone.now()
        if obj.next_run <= now:
            return 0
        
        delta = obj.next_run - now
        return round(delta.total_seconds() / 3600, 1)


class ReportShareSerializer(serializers.ModelSerializer):
    """Serializer for ReportShare model."""
    
    report_name = serializers.ReadOnlyField(source='report.name')
    shared_by_name = serializers.ReadOnlyField(source='shared_by.get_full_name')
    shared_with_name = serializers.ReadOnlyField(source='shared_with_user.get_full_name')
    is_expired_flag = serializers.SerializerMethodField()
    
    class Meta:
        model = ReportShare
        fields = [
            'id', 'shared_with_email', 'shared_with_user', 'access_level',
            'expires_at', 'access_count', 'last_accessed', 'report_name',
            'shared_by_name', 'shared_with_name', 'is_expired_flag',
            'created_at'
        ]
        read_only_fields = [
            'id', 'access_count', 'last_accessed', 'report_name',
            'shared_by_name', 'shared_with_name', 'is_expired_flag',
            'created_at'
        ]
    
    def get_is_expired_flag(self, obj):
        """Check if share is expired."""
        return obj.is_expired()


class ReportMetricSerializer(serializers.ModelSerializer):
    """Serializer for ReportMetric model."""
    
    tenant_name = serializers.ReadOnlyField(source='tenant.name')
    created_by_name = serializers.ReadOnlyField(source='created_by.get_full_name')
    
    class Meta:
        model = ReportMetric
        fields = [
            'id', 'name', 'description', 'metric_type', 'source_model',
            'source_field', 'calculation', 'filters', 'format_string',
            'tenant_name', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'tenant_name', 'created_by_name', 'created_at', 'updated_at'
        ]


class ReportGenerateSerializer(serializers.Serializer):
    """Serializer for generating reports."""
    
    template_id = serializers.UUIDField()
    name = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    period_start = serializers.DateTimeField(required=False)
    period_end = serializers.DateTimeField(required=False)
    export_format = serializers.ChoiceField(
        choices=[('json', 'JSON'), ('csv', 'CSV'), ('xlsx', 'Excel'), ('pdf', 'PDF')],
        default='json'
    )
    filters = serializers.JSONField(required=False, default=dict)
    
    def validate_template_id(self, value):
        """Validate template exists and user has access."""
        from .models import ReportTemplate
        
        try:
            template = ReportTemplate.objects.get(id=value)
            # Check if user has access to the template
            request = self.context.get('request')
            if request and hasattr(request, 'tenant'):
                if template.tenant != request.tenant:
                    raise serializers.ValidationError(
                        _("Template not found or access denied")
                    )
                if not template.is_public and template.created_by != request.user:
                    raise serializers.ValidationError(
                        _("Template not found or access denied")
                    )
        except ReportTemplate.DoesNotExist:
            raise serializers.ValidationError(_("Template not found"))
        
        return value
    
    def validate(self, attrs):
        """Validate date range if provided."""
        period_start = attrs.get('period_start')
        period_end = attrs.get('period_end')
        
        if period_start and period_end:
            if period_start >= period_end:
                raise serializers.ValidationError(
                    _("Period start must be before period end")
                )
        
        return attrs


class ReportTemplateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating report templates."""
    
    class Meta:
        model = ReportTemplate
        fields = [
            'name', 'description', 'report_type', 'data_sources',
            'filters', 'chart_config', 'columns', 'metrics', 'is_public'
        ]
    
    def validate_data_sources(self, value):
        """Validate data sources format."""
        if not isinstance(value, list):
            raise serializers.ValidationError(
                _("Data sources must be a list")
            )
        return value
    
    def validate_columns(self, value):
        """Validate columns format."""
        if not isinstance(value, list):
            raise serializers.ValidationError(
                _("Columns must be a list")
            )
        return value


class ScheduledReportCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating scheduled reports."""
    
    class Meta:
        model = ScheduledReport
        fields = [
            'name', 'description', 'template', 'schedule_type',
            'cron_expression', 'recipients', 'export_formats'
        ]
    
    def validate_recipients(self, value):
        """Validate recipients format."""
        if not isinstance(value, list):
            raise serializers.ValidationError(
                _("Recipients must be a list")
            )
        
        # Validate email addresses
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        for email in value:
            try:
                validate_email(email)
            except ValidationError:
                raise serializers.ValidationError(
                    _(f"Invalid email address: {email}")
                )
        
        return value
    
    def validate_export_formats(self, value):
        """Validate export formats."""
        if not isinstance(value, list):
            raise serializers.ValidationError(
                _("Export formats must be a list")
            )
        
        valid_formats = ['json', 'csv', 'xlsx', 'pdf']
        for format_type in value:
            if format_type not in valid_formats:
                raise serializers.ValidationError(
                    _(f"Invalid export format: {format_type}")
                )
        
        return value
    
    def validate(self, attrs):
        """Validate schedule configuration."""
        schedule_type = attrs.get('schedule_type')
        cron_expression = attrs.get('cron_expression')
        
        if schedule_type == 'custom' and not cron_expression:
            raise serializers.ValidationError(
                _("Cron expression is required for custom schedules")
            )
        
        return attrs


class ReportShareCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating report shares."""
    
    class Meta:
        model = ReportShare
        fields = [
            'report', 'shared_with_email', 'shared_with_user',
            'access_level', 'expires_at'
        ]
    
    def validate(self, attrs):
        """Validate that either email or user is provided."""
        shared_with_email = attrs.get('shared_with_email')
        shared_with_user = attrs.get('shared_with_user')
        
        if not shared_with_email and not shared_with_user:
            raise serializers.ValidationError(
                _("Either email or user must be provided")
            )
        
        if shared_with_email and shared_with_user:
            raise serializers.ValidationError(
                _("Provide either email or user, not both")
            )
        
        return attrs
