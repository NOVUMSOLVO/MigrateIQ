"""
Serializers for compliance models.
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .compliance import (
    DataRetentionPolicy, DataProcessingRecord, ConsentRecord,
    DataSubjectRequest, ComplianceReport
)


class DataRetentionPolicySerializer(serializers.ModelSerializer):
    """Serializer for DataRetentionPolicy model."""
    
    tenant_name = serializers.ReadOnlyField(source='tenant.name')
    
    class Meta:
        model = DataRetentionPolicy
        fields = [
            'id', 'name', 'description', 'data_type', 'retention_period_days',
            'auto_delete', 'anonymize_before_delete', 'is_active',
            'tenant_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant_name', 'created_at', 'updated_at']


class DataProcessingRecordSerializer(serializers.ModelSerializer):
    """Serializer for DataProcessingRecord model."""
    
    tenant_name = serializers.ReadOnlyField(source='tenant.name')
    
    class Meta:
        model = DataProcessingRecord
        fields = [
            'id', 'name', 'purpose', 'legal_basis', 'data_categories',
            'data_subjects', 'recipients', 'third_country_transfers',
            'transfer_safeguards', 'retention_period', 'security_measures',
            'tenant_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant_name', 'created_at', 'updated_at']


class ConsentRecordSerializer(serializers.ModelSerializer):
    """Serializer for ConsentRecord model."""
    
    user_name = serializers.ReadOnlyField(source='user.get_full_name')
    user_email = serializers.ReadOnlyField(source='user.email')
    tenant_name = serializers.ReadOnlyField(source='tenant.name')
    
    class Meta:
        model = ConsentRecord
        fields = [
            'id', 'purpose', 'consent_given', 'consent_text', 'ip_address',
            'user_agent', 'given_at', 'withdrawn_at', 'user_name',
            'user_email', 'tenant_name'
        ]
        read_only_fields = [
            'id', 'given_at', 'withdrawn_at', 'user_name', 'user_email',
            'tenant_name'
        ]


class DataSubjectRequestSerializer(serializers.ModelSerializer):
    """Serializer for DataSubjectRequest model."""
    
    tenant_name = serializers.ReadOnlyField(source='tenant.name')
    assigned_to_name = serializers.ReadOnlyField(source='assigned_to.get_full_name')
    is_overdue_flag = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = DataSubjectRequest
        fields = [
            'id', 'requester_email', 'requester_name', 'request_type',
            'description', 'status', 'assigned_to', 'response',
            'created_at', 'due_date', 'completed_at', 'tenant_name',
            'assigned_to_name', 'is_overdue_flag', 'days_remaining'
        ]
        read_only_fields = [
            'id', 'created_at', 'due_date', 'completed_at', 'tenant_name',
            'assigned_to_name', 'is_overdue_flag', 'days_remaining'
        ]
    
    def get_is_overdue_flag(self, obj):
        """Check if request is overdue."""
        return obj.is_overdue()
    
    def get_days_remaining(self, obj):
        """Get days remaining until due date."""
        from django.utils import timezone
        if obj.status == 'completed':
            return None
        
        now = timezone.now()
        if now > obj.due_date:
            return 0
        
        return (obj.due_date - now).days


class ComplianceReportSerializer(serializers.ModelSerializer):
    """Serializer for ComplianceReport model."""
    
    tenant_name = serializers.ReadOnlyField(source='tenant.name')
    generated_by_name = serializers.ReadOnlyField(source='generated_by.get_full_name')
    
    class Meta:
        model = ComplianceReport
        fields = [
            'id', 'name', 'report_type', 'report_data', 'period_start',
            'period_end', 'created_at', 'tenant_name', 'generated_by_name'
        ]
        read_only_fields = [
            'id', 'created_at', 'tenant_name', 'generated_by_name'
        ]


class ConsentWithdrawalSerializer(serializers.Serializer):
    """Serializer for withdrawing consent."""
    
    purpose = serializers.CharField(required=True)
    reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate_purpose(self, value):
        """Validate that the purpose exists for the user."""
        user = self.context['request'].user
        tenant = getattr(self.context['request'], 'tenant', None)
        
        if not ConsentRecord.objects.filter(
            user=user,
            tenant=tenant,
            purpose=value,
            consent_given=True
        ).exists():
            raise serializers.ValidationError(
                _("No active consent found for this purpose")
            )
        
        return value


class DataSubjectRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating data subject requests."""
    
    class Meta:
        model = DataSubjectRequest
        fields = [
            'requester_email', 'requester_name', 'request_type', 'description'
        ]
    
    def validate_requester_email(self, value):
        """Validate requester email."""
        # Add any email validation logic here
        return value


class GDPRDataExportSerializer(serializers.Serializer):
    """Serializer for GDPR data export requests."""
    
    include_personal_data = serializers.BooleanField(default=True)
    include_activity_logs = serializers.BooleanField(default=True)
    include_project_data = serializers.BooleanField(default=False)
    format = serializers.ChoiceField(
        choices=[('json', 'JSON'), ('csv', 'CSV'), ('xml', 'XML')],
        default='json'
    )
    
    def validate(self, attrs):
        """Validate that at least one data type is selected."""
        if not any([
            attrs.get('include_personal_data'),
            attrs.get('include_activity_logs'),
            attrs.get('include_project_data')
        ]):
            raise serializers.ValidationError(
                _("At least one data type must be selected for export")
            )
        return attrs


class ComplianceReportGenerateSerializer(serializers.Serializer):
    """Serializer for generating compliance reports."""
    
    report_type = serializers.ChoiceField(
        choices=[
            ('gdpr_compliance', _('GDPR Compliance')),
            ('data_retention', _('Data Retention')),
            ('consent_overview', _('Consent Overview')),
            ('data_subject_requests', _('Data Subject Requests')),
            ('security_audit', _('Security Audit')),
        ]
    )
    period_start = serializers.DateTimeField()
    period_end = serializers.DateTimeField()
    include_details = serializers.BooleanField(default=True)
    format = serializers.ChoiceField(
        choices=[('json', 'JSON'), ('pdf', 'PDF'), ('csv', 'CSV')],
        default='json'
    )
    
    def validate(self, attrs):
        """Validate date range."""
        if attrs['period_start'] >= attrs['period_end']:
            raise serializers.ValidationError(
                _("Period start must be before period end")
            )
        return attrs


class DataRetentionPolicyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating data retention policies."""
    
    class Meta:
        model = DataRetentionPolicy
        fields = [
            'name', 'description', 'data_type', 'retention_period_days',
            'auto_delete', 'anonymize_before_delete'
        ]
    
    def validate_retention_period_days(self, value):
        """Validate retention period."""
        if value < 0:
            raise serializers.ValidationError(
                _("Retention period cannot be negative")
            )
        return value


class DataProcessingRecordCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating data processing records."""
    
    class Meta:
        model = DataProcessingRecord
        fields = [
            'name', 'purpose', 'legal_basis', 'data_categories',
            'data_subjects', 'recipients', 'third_country_transfers',
            'transfer_safeguards', 'retention_period', 'security_measures'
        ]
    
    def validate_data_categories(self, value):
        """Validate data categories format."""
        if not isinstance(value, list):
            raise serializers.ValidationError(
                _("Data categories must be a list")
            )
        return value
    
    def validate_data_subjects(self, value):
        """Validate data subjects format."""
        if not isinstance(value, list):
            raise serializers.ValidationError(
                _("Data subjects must be a list")
            )
        return value
