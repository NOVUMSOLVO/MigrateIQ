"""
NHS Compliance Serializers

Serializers for NHS compliance models and data structures.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    NHSOrganization, DSPTAssessment, CQCAuditTrail,
    PatientSafetyIncident, ComplianceChecklist
)

User = get_user_model()


class NHSOrganizationSerializer(serializers.ModelSerializer):
    """Serializer for NHS Organization."""
    
    dspt_status_display = serializers.CharField(source='get_dspt_status_display', read_only=True)
    organization_type_display = serializers.CharField(source='get_organization_type_display', read_only=True)
    
    class Meta:
        model = NHSOrganization
        fields = [
            'id', 'ods_code', 'organization_name', 'organization_type',
            'organization_type_display', 'primary_contact_name',
            'primary_contact_email', 'primary_contact_phone',
            'dspt_status', 'dspt_status_display', 'dspt_expiry_date',
            'cqc_registration_number', 'data_protection_officer',
            'caldicott_guardian', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_ods_code(self, value):
        """Validate ODS code format."""
        import re
        if not re.match(r'^[A-Z0-9]{3,10}$', value):
            raise serializers.ValidationError(
                "ODS code must be 3-10 characters, uppercase letters and numbers only"
            )
        return value


class DSPTAssessmentSerializer(serializers.ModelSerializer):
    """Serializer for DSPT Assessment."""
    
    overall_status_display = serializers.CharField(source='get_overall_status_display', read_only=True)
    organization_name = serializers.CharField(source='organization.organization_name', read_only=True)
    
    class Meta:
        model = DSPTAssessment
        fields = [
            'id', 'organization', 'organization_name', 'assessment_year',
            'submission_date', 'mandatory_evidence_complete',
            'data_security_score', 'staff_responsibilities_score',
            'training_score', 'overall_status', 'overall_status_display',
            'compliance_notes', 'action_plan', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'organization_name']
    
    def validate_assessment_year(self, value):
        """Validate assessment year format."""
        import re
        if not re.match(r'^\d{4}-\d{4}$', value):
            raise serializers.ValidationError(
                "Assessment year must be in format YYYY-YYYY (e.g., 2023-2024)"
            )
        return value
    
    def validate(self, data):
        """Validate score ranges."""
        score_fields = ['data_security_score', 'staff_responsibilities_score', 'training_score']
        for field in score_fields:
            score = data.get(field, 0)
            if score < 0 or score > 100:
                raise serializers.ValidationError(
                    f"{field} must be between 0 and 100"
                )
        return data


class CQCAuditTrailSerializer(serializers.ModelSerializer):
    """Serializer for CQC Audit Trail."""
    
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    resolution_status_display = serializers.CharField(source='get_resolution_status_display', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    organization_name = serializers.CharField(source='organization.organization_name', read_only=True)
    
    class Meta:
        model = CQCAuditTrail
        fields = [
            'id', 'audit_id', 'organization', 'organization_name',
            'event_timestamp', 'category', 'category_display',
            'severity', 'severity_display', 'user', 'user_name',
            'user_role', 'system_component', 'event_description',
            'technical_details', 'patient_data_affected',
            'patient_count_affected', 'clinical_impact_assessment',
            'immediate_action_taken', 'resolution_status',
            'resolution_status_display', 'resolution_timestamp',
            'lessons_learned', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'audit_id', 'created_at', 'updated_at',
            'user_name', 'organization_name'
        ]


class PatientSafetyIncidentSerializer(serializers.ModelSerializer):
    """Serializer for Patient Safety Incident."""
    
    incident_type_display = serializers.CharField(source='get_incident_type_display', read_only=True)
    harm_level_display = serializers.CharField(source='get_harm_level_display', read_only=True)
    investigation_status_display = serializers.CharField(source='get_investigation_status_display', read_only=True)
    reported_by_name = serializers.CharField(source='reported_by.get_full_name', read_only=True)
    organization_name = serializers.CharField(source='organization.organization_name', read_only=True)
    
    class Meta:
        model = PatientSafetyIncident
        fields = [
            'id', 'incident_id', 'organization', 'organization_name',
            'incident_date', 'incident_type', 'incident_type_display',
            'incident_description', 'patients_affected', 'harm_level',
            'harm_level_display', 'clinical_consequences',
            'reported_by', 'reported_by_name', 'reported_date',
            'investigation_required', 'investigation_status',
            'investigation_status_display', 'nrls_reported',
            'cqc_notified', 'ico_notified', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'incident_id', 'created_at', 'updated_at',
            'reported_by_name', 'organization_name'
        ]
    
    def validate_patients_affected(self, value):
        """Validate patients affected count."""
        if value < 0:
            raise serializers.ValidationError("Patients affected cannot be negative")
        return value


class ComplianceChecklistSerializer(serializers.ModelSerializer):
    """Serializer for Compliance Checklist."""
    
    organization_name = serializers.CharField(source='organization.organization_name', read_only=True)
    technical_signoff_name = serializers.CharField(source='technical_signoff.get_full_name', read_only=True)
    clinical_signoff_name = serializers.CharField(source='clinical_signoff.get_full_name', read_only=True)
    completion_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = ComplianceChecklist
        fields = [
            'id', 'organization', 'organization_name', 'project_name',
            # Pre-migration checks
            'risk_assessment_completed', 'data_mapping_validated',
            'backup_strategy_confirmed', 'rollback_plan_tested',
            # Security checks
            'encryption_verified', 'access_controls_tested',
            'audit_logging_enabled',
            # Compliance checks
            'dspt_compliance_verified', 'gdpr_assessment_completed',
            'caldicott_approval_obtained',
            # Post-migration checks
            'data_integrity_verified', 'system_performance_tested',
            'user_acceptance_completed',
            # Sign-off
            'technical_signoff', 'technical_signoff_name',
            'clinical_signoff', 'clinical_signoff_name',
            'completion_date', 'completion_percentage',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'organization_name',
            'technical_signoff_name', 'clinical_signoff_name',
            'completion_percentage'
        ]
    
    def get_completion_percentage(self, obj):
        """Calculate completion percentage."""
        checklist_fields = [
            'risk_assessment_completed', 'data_mapping_validated',
            'backup_strategy_confirmed', 'rollback_plan_tested',
            'encryption_verified', 'access_controls_tested',
            'audit_logging_enabled', 'dspt_compliance_verified',
            'gdpr_assessment_completed', 'caldicott_approval_obtained',
            'data_integrity_verified', 'system_performance_tested',
            'user_acceptance_completed'
        ]
        
        completed_count = sum(1 for field in checklist_fields if getattr(obj, field, False))
        total_count = len(checklist_fields)
        
        return round((completed_count / total_count) * 100, 1) if total_count > 0 else 0


class HealthcareDataValidationSerializer(serializers.Serializer):
    """Serializer for healthcare data validation requests."""
    
    data = serializers.JSONField(help_text="Healthcare data to validate")
    data_type = serializers.ChoiceField(
        choices=['HL7', 'FHIR', 'DICOM', 'NHS'],
        help_text="Type of healthcare data"
    )
    
    def validate_data(self, value):
        """Validate that data is provided."""
        if not value:
            raise serializers.ValidationError("Data cannot be empty")
        return value


class PatientDataEncryptionSerializer(serializers.Serializer):
    """Serializer for patient data encryption requests."""
    
    patient_data = serializers.JSONField(help_text="Patient data to encrypt")
    nhs_number = serializers.CharField(
        max_length=10,
        min_length=10,
        help_text="NHS Number (10 digits)"
    )
    
    def validate_nhs_number(self, value):
        """Validate NHS Number format."""
        import re
        # Remove spaces and hyphens
        nhs_number = re.sub(r'[\s-]', '', value)
        
        if not re.match(r'^\d{10}$', nhs_number):
            raise serializers.ValidationError("NHS Number must be exactly 10 digits")
        
        return nhs_number
    
    def validate_patient_data(self, value):
        """Validate patient data structure."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Patient data must be a JSON object")
        
        if not value:
            raise serializers.ValidationError("Patient data cannot be empty")
        
        return value


class DSPTComplianceReportSerializer(serializers.Serializer):
    """Serializer for DSPT compliance reports."""
    
    organization_id = serializers.IntegerField()
    assessment_year = serializers.CharField(max_length=9)
    report_type = serializers.ChoiceField(
        choices=['SUMMARY', 'DETAILED', 'ACTION_PLAN'],
        default='SUMMARY'
    )
    include_evidence = serializers.BooleanField(default=False)
    
    def validate_assessment_year(self, value):
        """Validate assessment year format."""
        import re
        if not re.match(r'^\d{4}-\d{4}$', value):
            raise serializers.ValidationError(
                "Assessment year must be in format YYYY-YYYY"
            )
        return value


class AuditTrailFilterSerializer(serializers.Serializer):
    """Serializer for audit trail filtering."""
    
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    category = serializers.ChoiceField(
        choices=CQCAuditTrail.AUDIT_CATEGORIES,
        required=False
    )
    severity = serializers.ChoiceField(
        choices=CQCAuditTrail.SEVERITY_LEVELS,
        required=False
    )
    user_id = serializers.IntegerField(required=False)
    patient_data_affected = serializers.BooleanField(required=False)
    
    def validate(self, data):
        """Validate date range."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                "Start date must be before end date"
            )
        
        return data
