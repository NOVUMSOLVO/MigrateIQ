"""
NHS Compliance Models

Models for managing NHS and CQC compliance requirements in data migration.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import RegexValidator
from core.models import TimeStampedModel, Tenant
import uuid

User = get_user_model()


class NHSOrganization(TimeStampedModel):
    """Model for NHS organizations and trusts."""

    ORGANIZATION_TYPES = [
        ('NHS_TRUST', 'NHS Trust'),
        ('NHS_FOUNDATION_TRUST', 'NHS Foundation Trust'),
        ('CCG', 'Clinical Commissioning Group'),
        ('ICB', 'Integrated Care Board'),
        ('GP_PRACTICE', 'GP Practice'),
        ('PRIVATE_HEALTHCARE', 'Private Healthcare Provider'),
    ]

    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='nhs_organization')

    # NHS Organization Details
    ods_code = models.CharField(
        _('ODS Code'),
        max_length=10,
        unique=True,
        validators=[RegexValidator(r'^[A-Z0-9]{3,10}$', 'Invalid ODS code format')],
        help_text=_('NHS Organization Data Service code')
    )

    organization_name = models.CharField(_('Organization Name'), max_length=255)
    organization_type = models.CharField(_('Organization Type'), max_length=30, choices=ORGANIZATION_TYPES)

    # Contact Information
    primary_contact_name = models.CharField(_('Primary Contact Name'), max_length=255)
    primary_contact_email = models.EmailField(_('Primary Contact Email'))
    primary_contact_phone = models.CharField(_('Primary Contact Phone'), max_length=20)

    # Compliance Information
    dspt_status = models.CharField(
        _('DSPT Status'),
        max_length=20,
        choices=[
            ('COMPLIANT', 'Compliant'),
            ('NON_COMPLIANT', 'Non-Compliant'),
            ('IN_PROGRESS', 'In Progress'),
            ('EXPIRED', 'Expired'),
        ],
        default='IN_PROGRESS'
    )

    dspt_expiry_date = models.DateField(_('DSPT Expiry Date'), null=True, blank=True)
    cqc_registration_number = models.CharField(_('CQC Registration Number'), max_length=20, blank=True)

    # Risk Assessment
    data_protection_officer = models.CharField(_('Data Protection Officer'), max_length=255)
    caldicott_guardian = models.CharField(_('Caldicott Guardian'), max_length=255)

    class Meta:
        verbose_name = _('NHS Organization')
        verbose_name_plural = _('NHS Organizations')

    def __str__(self):
        return f"{self.organization_name} ({self.ods_code})"


class DSPTAssessment(TimeStampedModel):
    """Data Security and Protection Toolkit assessment."""

    organization = models.ForeignKey(NHSOrganization, on_delete=models.CASCADE, related_name='dspt_assessments')

    # Assessment Details
    assessment_year = models.CharField(_('Assessment Year'), max_length=9)  # e.g., "2023-2024"
    submission_date = models.DateTimeField(_('Submission Date'), null=True, blank=True)

    # Mandatory Evidence Items
    mandatory_evidence_complete = models.BooleanField(_('Mandatory Evidence Complete'), default=False)

    # Assertion Scores
    data_security_score = models.IntegerField(_('Data Security Score'), default=0)
    staff_responsibilities_score = models.IntegerField(_('Staff Responsibilities Score'), default=0)
    training_score = models.IntegerField(_('Training Score'), default=0)

    # Overall Status
    overall_status = models.CharField(
        _('Overall Status'),
        max_length=20,
        choices=[
            ('STANDARDS_MET', 'Standards Met'),
            ('STANDARDS_NOT_MET', 'Standards Not Met'),
            ('PLAN_AGREED', 'Plan Agreed'),
            ('IN_PROGRESS', 'In Progress'),
        ],
        default='IN_PROGRESS'
    )

    # Compliance Notes
    compliance_notes = models.TextField(_('Compliance Notes'), blank=True)
    action_plan = models.TextField(_('Action Plan'), blank=True)

    class Meta:
        verbose_name = _('DSPT Assessment')
        verbose_name_plural = _('DSPT Assessments')
        unique_together = [['organization', 'assessment_year']]


class CQCAuditTrail(TimeStampedModel):
    """CQC-compliant audit trail for migration activities."""

    AUDIT_CATEGORIES = [
        ('PATIENT_SAFETY', 'Patient Safety'),
        ('DATA_INTEGRITY', 'Data Integrity'),
        ('ACCESS_CONTROL', 'Access Control'),
        ('SYSTEM_CHANGE', 'System Change'),
        ('INCIDENT', 'Incident'),
        ('COMPLIANCE', 'Compliance'),
    ]

    SEVERITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    # Basic Information
    audit_id = models.UUIDField(_('Audit ID'), default=uuid.uuid4, unique=True)
    organization = models.ForeignKey(NHSOrganization, on_delete=models.CASCADE, related_name='audit_trails')

    # Event Details
    event_timestamp = models.DateTimeField(_('Event Timestamp'), default=timezone.now)
    category = models.CharField(_('Category'), max_length=20, choices=AUDIT_CATEGORIES)
    severity = models.CharField(_('Severity'), max_length=10, choices=SEVERITY_LEVELS)

    # User and System Information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    user_role = models.CharField(_('User Role'), max_length=100, blank=True)
    system_component = models.CharField(_('System Component'), max_length=100)

    # Event Description
    event_description = models.TextField(_('Event Description'))
    technical_details = models.JSONField(_('Technical Details'), default=dict)

    # Patient Impact Assessment
    patient_data_affected = models.BooleanField(_('Patient Data Affected'), default=False)
    patient_count_affected = models.PositiveIntegerField(_('Patient Count Affected'), default=0)
    clinical_impact_assessment = models.TextField(_('Clinical Impact Assessment'), blank=True)

    # Response and Resolution
    immediate_action_taken = models.TextField(_('Immediate Action Taken'), blank=True)
    resolution_status = models.CharField(
        _('Resolution Status'),
        max_length=20,
        choices=[
            ('OPEN', 'Open'),
            ('IN_PROGRESS', 'In Progress'),
            ('RESOLVED', 'Resolved'),
            ('CLOSED', 'Closed'),
        ],
        default='OPEN'
    )

    resolution_timestamp = models.DateTimeField(_('Resolution Timestamp'), null=True, blank=True)
    lessons_learned = models.TextField(_('Lessons Learned'), blank=True)

    class Meta:
        verbose_name = _('CQC Audit Trail')
        verbose_name_plural = _('CQC Audit Trails')
        ordering = ['-event_timestamp']


class PatientSafetyIncident(TimeStampedModel):
    """Patient safety incidents related to data migration."""

    INCIDENT_TYPES = [
        ('DATA_LOSS', 'Data Loss'),
        ('DATA_CORRUPTION', 'Data Corruption'),
        ('UNAUTHORIZED_ACCESS', 'Unauthorized Access'),
        ('SYSTEM_DOWNTIME', 'System Downtime'),
        ('INCORRECT_MAPPING', 'Incorrect Data Mapping'),
        ('DELAYED_MIGRATION', 'Delayed Migration'),
    ]

    HARM_LEVELS = [
        ('NO_HARM', 'No Harm'),
        ('LOW_HARM', 'Low Harm'),
        ('MODERATE_HARM', 'Moderate Harm'),
        ('SEVERE_HARM', 'Severe Harm'),
        ('DEATH', 'Death'),
    ]

    # Incident Identification
    incident_id = models.UUIDField(_('Incident ID'), default=uuid.uuid4, unique=True)
    organization = models.ForeignKey(NHSOrganization, on_delete=models.CASCADE, related_name='safety_incidents')

    # Incident Details
    incident_date = models.DateTimeField(_('Incident Date'))
    incident_type = models.CharField(_('Incident Type'), max_length=30, choices=INCIDENT_TYPES)
    incident_description = models.TextField(_('Incident Description'))

    # Patient Impact
    patients_affected = models.PositiveIntegerField(_('Patients Affected'), default=0)
    harm_level = models.CharField(_('Harm Level'), max_length=15, choices=HARM_LEVELS)
    clinical_consequences = models.TextField(_('Clinical Consequences'), blank=True)

    # Reporting
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reported_incidents')
    reported_date = models.DateTimeField(_('Reported Date'), default=timezone.now)

    # Investigation
    investigation_required = models.BooleanField(_('Investigation Required'), default=True)
    investigation_status = models.CharField(
        _('Investigation Status'),
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('IN_PROGRESS', 'In Progress'),
            ('COMPLETED', 'Completed'),
            ('CLOSED', 'Closed'),
        ],
        default='PENDING'
    )

    # External Reporting
    nrls_reported = models.BooleanField(_('NRLS Reported'), default=False)
    cqc_notified = models.BooleanField(_('CQC Notified'), default=False)
    ico_notified = models.BooleanField(_('ICO Notified'), default=False)

    class Meta:
        verbose_name = _('Patient Safety Incident')
        verbose_name_plural = _('Patient Safety Incidents')
        ordering = ['-incident_date']


class ComplianceChecklist(TimeStampedModel):
    """Compliance checklist for migration projects."""

    organization = models.ForeignKey(NHSOrganization, on_delete=models.CASCADE, related_name='compliance_checklists')
    project_name = models.CharField(_('Project Name'), max_length=255)

    # Pre-Migration Checks
    risk_assessment_completed = models.BooleanField(_('Risk Assessment Completed'), default=False)
    data_mapping_validated = models.BooleanField(_('Data Mapping Validated'), default=False)
    backup_strategy_confirmed = models.BooleanField(_('Backup Strategy Confirmed'), default=False)
    rollback_plan_tested = models.BooleanField(_('Rollback Plan Tested'), default=False)

    # Security Checks
    encryption_verified = models.BooleanField(_('Encryption Verified'), default=False)
    access_controls_tested = models.BooleanField(_('Access Controls Tested'), default=False)
    audit_logging_enabled = models.BooleanField(_('Audit Logging Enabled'), default=False)

    # Compliance Checks
    dspt_compliance_verified = models.BooleanField(_('DSPT Compliance Verified'), default=False)
    gdpr_assessment_completed = models.BooleanField(_('GDPR Assessment Completed'), default=False)
    caldicott_approval_obtained = models.BooleanField(_('Caldicott Approval Obtained'), default=False)

    # Post-Migration Checks
    data_integrity_verified = models.BooleanField(_('Data Integrity Verified'), default=False)
    system_performance_tested = models.BooleanField(_('System Performance Tested'), default=False)
    user_acceptance_completed = models.BooleanField(_('User Acceptance Completed'), default=False)

    # Sign-off
    technical_signoff = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='technical_signoffs'
    )
    clinical_signoff = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clinical_signoffs'
    )

    completion_date = models.DateTimeField(_('Completion Date'), null=True, blank=True)

    class Meta:
        verbose_name = _('Compliance Checklist')
        verbose_name_plural = _('Compliance Checklists')
