"""
NHS Compliance Views

API endpoints for NHS and CQC compliance management.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from django.utils import timezone
from django.db.models import Q, Count
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import (
    NHSOrganization, DSPTAssessment, CQCAuditTrail,
    PatientSafetyIncident, ComplianceChecklist
)
from .serializers import (
    NHSOrganizationSerializer, DSPTAssessmentSerializer,
    CQCAuditTrailSerializer, PatientSafetyIncidentSerializer,
    ComplianceChecklistSerializer
)
from healthcare_standards.validators import HealthcareDataValidator
from core.encryption import nhs_encryption

logger = logging.getLogger(__name__)


class NHSComplianceDashboardView(APIView):
    """NHS compliance dashboard with key metrics and status."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get NHS compliance dashboard data",
        description="Returns comprehensive NHS compliance metrics and status information",
        responses={200: dict}
    )
    def get(self, request):
        """Get NHS compliance dashboard data."""
        try:
            # Get user's NHS organization
            nhs_org = self._get_user_nhs_organization(request.user)
            if not nhs_org:
                return Response(
                    {'error': 'No NHS organization found for user'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Calculate dashboard metrics
            dashboard_data = {
                'organization': NHSOrganizationSerializer(nhs_org).data,
                'dspt_status': self._get_dspt_status(nhs_org),
                'audit_summary': self._get_audit_summary(nhs_org),
                'safety_incidents': self._get_safety_incidents_summary(nhs_org),
                'compliance_score': self._calculate_compliance_score(nhs_org),
                'recent_activities': self._get_recent_activities(nhs_org),
                'alerts': self._get_compliance_alerts(nhs_org),
            }

            return Response(dashboard_data)

        except Exception as e:
            logger.error(f"Error generating NHS compliance dashboard: {str(e)}")
            return Response(
                {'error': 'Failed to generate compliance dashboard'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_user_nhs_organization(self, user):
        """Get NHS organization for the user."""
        try:
            return NHSOrganization.objects.get(tenant=user.tenant)
        except NHSOrganization.DoesNotExist:
            return None

    def _get_dspt_status(self, nhs_org):
        """Get DSPT assessment status."""
        latest_assessment = DSPTAssessment.objects.filter(
            organization=nhs_org
        ).order_by('-assessment_year').first()

        if not latest_assessment:
            return {
                'status': 'NOT_ASSESSED',
                'message': 'No DSPT assessment found',
                'expiry_date': None,
                'days_until_expiry': None,
            }

        # Calculate days until expiry
        days_until_expiry = None
        if nhs_org.dspt_expiry_date:
            days_until_expiry = (nhs_org.dspt_expiry_date - timezone.now().date()).days

        return {
            'status': nhs_org.dspt_status,
            'assessment_year': latest_assessment.assessment_year,
            'overall_status': latest_assessment.overall_status,
            'expiry_date': nhs_org.dspt_expiry_date,
            'days_until_expiry': days_until_expiry,
            'scores': {
                'data_security': latest_assessment.data_security_score,
                'staff_responsibilities': latest_assessment.staff_responsibilities_score,
                'training': latest_assessment.training_score,
            }
        }

    def _get_audit_summary(self, nhs_org):
        """Get audit trail summary."""
        thirty_days_ago = timezone.now() - timedelta(days=30)

        audit_counts = CQCAuditTrail.objects.filter(
            organization=nhs_org,
            event_timestamp__gte=thirty_days_ago
        ).aggregate(
            total=Count('id'),
            critical=Count('id', filter=Q(severity='CRITICAL')),
            high=Count('id', filter=Q(severity='HIGH')),
            medium=Count('id', filter=Q(severity='MEDIUM')),
            low=Count('id', filter=Q(severity='LOW')),
        )

        return {
            'last_30_days': audit_counts,
            'categories': list(
                CQCAuditTrail.objects.filter(
                    organization=nhs_org,
                    event_timestamp__gte=thirty_days_ago
                ).values_list('category', flat=True).distinct()
            )
        }

    def _get_safety_incidents_summary(self, nhs_org):
        """Get patient safety incidents summary."""
        thirty_days_ago = timezone.now() - timedelta(days=30)

        incident_counts = PatientSafetyIncident.objects.filter(
            organization=nhs_org,
            incident_date__gte=thirty_days_ago
        ).aggregate(
            total=Count('id'),
            open=Count('id', filter=Q(investigation_status__in=['PENDING', 'IN_PROGRESS'])),
            closed=Count('id', filter=Q(investigation_status='CLOSED')),
        )

        # Get incidents by harm level
        harm_levels = PatientSafetyIncident.objects.filter(
            organization=nhs_org,
            incident_date__gte=thirty_days_ago
        ).values('harm_level').annotate(count=Count('id'))

        return {
            'last_30_days': incident_counts,
            'by_harm_level': {item['harm_level']: item['count'] for item in harm_levels},
        }

    def _calculate_compliance_score(self, nhs_org):
        """Calculate overall compliance score."""
        score = 0
        max_score = 100

        # DSPT compliance (40 points)
        if nhs_org.dspt_status == 'COMPLIANT':
            score += 40
        elif nhs_org.dspt_status == 'IN_PROGRESS':
            score += 20

        # Recent audit activity (20 points)
        recent_audits = CQCAuditTrail.objects.filter(
            organization=nhs_org,
            event_timestamp__gte=timezone.now() - timedelta(days=7)
        ).count()
        if recent_audits > 0:
            score += min(20, recent_audits * 2)

        # Safety incident management (20 points)
        open_incidents = PatientSafetyIncident.objects.filter(
            organization=nhs_org,
            investigation_status__in=['PENDING', 'IN_PROGRESS']
        ).count()
        if open_incidents == 0:
            score += 20
        elif open_incidents <= 2:
            score += 10

        # Compliance checklists (20 points)
        completed_checklists = ComplianceChecklist.objects.filter(
            organization=nhs_org,
            completion_date__isnull=False
        ).count()
        if completed_checklists > 0:
            score += min(20, completed_checklists * 5)

        return {
            'score': score,
            'max_score': max_score,
            'percentage': round((score / max_score) * 100, 1),
            'grade': self._get_compliance_grade(score, max_score),
        }

    def _get_compliance_grade(self, score, max_score):
        """Get compliance grade based on score."""
        percentage = (score / max_score) * 100
        if percentage >= 90:
            return 'A'
        elif percentage >= 80:
            return 'B'
        elif percentage >= 70:
            return 'C'
        elif percentage >= 60:
            return 'D'
        else:
            return 'F'

    def _get_recent_activities(self, nhs_org):
        """Get recent compliance activities."""
        recent_audits = CQCAuditTrail.objects.filter(
            organization=nhs_org
        ).order_by('-event_timestamp')[:5]

        return CQCAuditTrailSerializer(recent_audits, many=True).data

    def _get_compliance_alerts(self, nhs_org):
        """Get compliance alerts and warnings."""
        alerts = []

        # DSPT expiry warning
        if nhs_org.dspt_expiry_date:
            days_until_expiry = (nhs_org.dspt_expiry_date - timezone.now().date()).days
            if days_until_expiry <= 30:
                alerts.append({
                    'type': 'warning' if days_until_expiry > 7 else 'critical',
                    'title': 'DSPT Expiry Warning',
                    'message': f'DSPT expires in {days_until_expiry} days',
                    'action_required': 'Renew DSPT assessment',
                })

        # Open safety incidents
        open_incidents = PatientSafetyIncident.objects.filter(
            organization=nhs_org,
            investigation_status__in=['PENDING', 'IN_PROGRESS']
        ).count()
        if open_incidents > 0:
            alerts.append({
                'type': 'warning',
                'title': 'Open Safety Incidents',
                'message': f'{open_incidents} safety incidents require attention',
                'action_required': 'Review and close incidents',
            })

        # High severity audit events
        critical_audits = CQCAuditTrail.objects.filter(
            organization=nhs_org,
            severity='CRITICAL',
            resolution_status='OPEN',
            event_timestamp__gte=timezone.now() - timedelta(days=7)
        ).count()
        if critical_audits > 0:
            alerts.append({
                'type': 'critical',
                'title': 'Critical Audit Events',
                'message': f'{critical_audits} critical events need resolution',
                'action_required': 'Investigate and resolve critical events',
            })

        return alerts


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@extend_schema(
    summary="Validate healthcare data",
    description="Validate healthcare data against NHS standards (HL7, FHIR, DICOM)",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'data': {'type': 'object', 'description': 'Healthcare data to validate'},
                'data_type': {'type': 'string', 'enum': ['HL7', 'FHIR', 'DICOM', 'NHS']},
            },
            'required': ['data', 'data_type']
        }
    },
    responses={200: dict}
)
def validate_healthcare_data(request):
    """Validate healthcare data against NHS standards."""
    try:
        data = request.data.get('data')
        data_type = request.data.get('data_type')

        if not data or not data_type:
            return Response(
                {'error': 'Both data and data_type are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Initialize validator
        validator = HealthcareDataValidator()

        # Validate data
        is_valid, errors = validator.validate_healthcare_record(data, data_type)

        # Create audit trail for validation
        nhs_org = NHSOrganization.objects.filter(tenant=request.user.tenant).first()
        if nhs_org:
            CQCAuditTrail.objects.create(
                organization=nhs_org,
                category='DATA_INTEGRITY',
                severity='LOW',
                event_description=f'Healthcare data validation performed ({data_type})',
                technical_details={
                    'data_type': data_type,
                    'validation_result': is_valid,
                    'error_count': len(errors),
                },
                user=request.user,
                system_component='healthcare_validator',
            )

        return Response({
            'valid': is_valid,
            'errors': errors,
            'data_type': data_type,
            'validation_timestamp': timezone.now().isoformat(),
        })

    except Exception as e:
        logger.error(f"Healthcare data validation failed: {str(e)}")
        return Response(
            {'error': 'Validation failed', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@extend_schema(
    summary="Encrypt patient data",
    description="Encrypt patient data using NHS-compliant encryption",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'patient_data': {'type': 'object', 'description': 'Patient data to encrypt'},
                'nhs_number': {'type': 'string', 'description': 'NHS Number'},
            },
            'required': ['patient_data', 'nhs_number']
        }
    },
    responses={200: dict}
)
def encrypt_patient_data(request):
    """Encrypt patient data using NHS-compliant encryption."""
    try:
        patient_data = request.data.get('patient_data')
        nhs_number = request.data.get('nhs_number')

        if not patient_data or not nhs_number:
            return Response(
                {'error': 'Both patient_data and nhs_number are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate NHS Number first
        from healthcare_standards.validators import NHSNumberValidator
        is_valid, error_msg = NHSNumberValidator.validate(nhs_number)
        if not is_valid:
            return Response(
                {'error': f'Invalid NHS Number: {error_msg}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Encrypt patient data
        from core.encryption import patient_encryption
        encrypted_data = patient_encryption.encrypt_patient_data(patient_data, nhs_number)

        # Create audit trail
        nhs_org = NHSOrganization.objects.filter(tenant=request.user.tenant).first()
        if nhs_org:
            CQCAuditTrail.objects.create(
                organization=nhs_org,
                category='DATA_INTEGRITY',
                severity='MEDIUM',
                event_description='Patient data encrypted',
                technical_details={
                    'nhs_number_hash': encrypted_data.get('nhs_number_hash'),
                    'encryption_algorithm': encrypted_data.get('algorithm'),
                },
                user=request.user,
                system_component='patient_encryption',
                patient_data_affected=True,
                patient_count_affected=1,
            )

        return Response({
            'encrypted': True,
            'encrypted_data': encrypted_data,
            'encryption_timestamp': timezone.now().isoformat(),
        })

    except Exception as e:
        logger.error(f"Patient data encryption failed: {str(e)}")
        return Response(
            {'error': 'Encryption failed', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class DSPTAssessmentView(APIView):
    """DSPT assessment management."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get DSPT assessments for organization."""
        nhs_org = NHSOrganization.objects.filter(tenant=request.user.tenant).first()
        if not nhs_org:
            return Response(
                {'error': 'No NHS organization found'},
                status=status.HTTP_404_NOT_FOUND
            )

        assessments = DSPTAssessment.objects.filter(organization=nhs_org)
        serializer = DSPTAssessmentSerializer(assessments, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create new DSPT assessment."""
        nhs_org = NHSOrganization.objects.filter(tenant=request.user.tenant).first()
        if not nhs_org:
            return Response(
                {'error': 'No NHS organization found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = DSPTAssessmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(organization=nhs_org)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CQCAuditTrailListView(APIView):
    """List and create CQC audit trail entries."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get audit trail entries for organization."""
        nhs_org = NHSOrganization.objects.filter(tenant=request.user.tenant).first()
        if not nhs_org:
            return Response({'error': 'No NHS organization found'}, status=status.HTTP_404_NOT_FOUND)

        audit_trails = CQCAuditTrail.objects.filter(organization=nhs_org).order_by('-event_timestamp')
        serializer = CQCAuditTrailSerializer(audit_trails, many=True)
        return Response(serializer.data)


class CQCAuditTrailDetailView(APIView):
    """Retrieve specific audit trail entry."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, audit_id):
        """Get specific audit trail entry."""
        try:
            audit_trail = CQCAuditTrail.objects.get(audit_id=audit_id)
            serializer = CQCAuditTrailSerializer(audit_trail)
            return Response(serializer.data)
        except CQCAuditTrail.DoesNotExist:
            return Response({'error': 'Audit trail not found'}, status=status.HTTP_404_NOT_FOUND)


class PatientSafetyIncidentListView(APIView):
    """List and create patient safety incidents."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get safety incidents for organization."""
        nhs_org = NHSOrganization.objects.filter(tenant=request.user.tenant).first()
        if not nhs_org:
            return Response({'error': 'No NHS organization found'}, status=status.HTTP_404_NOT_FOUND)

        incidents = PatientSafetyIncident.objects.filter(organization=nhs_org).order_by('-incident_date')
        serializer = PatientSafetyIncidentSerializer(incidents, many=True)
        return Response(serializer.data)


class PatientSafetyIncidentDetailView(APIView):
    """Retrieve specific safety incident."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, incident_id):
        """Get specific safety incident."""
        try:
            incident = PatientSafetyIncident.objects.get(incident_id=incident_id)
            serializer = PatientSafetyIncidentSerializer(incident)
            return Response(serializer.data)
        except PatientSafetyIncident.DoesNotExist:
            return Response({'error': 'Safety incident not found'}, status=status.HTTP_404_NOT_FOUND)


class ComplianceChecklistListView(APIView):
    """List and create compliance checklists."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get compliance checklists for organization."""
        nhs_org = NHSOrganization.objects.filter(tenant=request.user.tenant).first()
        if not nhs_org:
            return Response({'error': 'No NHS organization found'}, status=status.HTTP_404_NOT_FOUND)

        checklists = ComplianceChecklist.objects.filter(organization=nhs_org)
        serializer = ComplianceChecklistSerializer(checklists, many=True)
        return Response(serializer.data)


class ComplianceChecklistDetailView(APIView):
    """Retrieve specific compliance checklist."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        """Get specific compliance checklist."""
        try:
            checklist = ComplianceChecklist.objects.get(pk=pk)
            serializer = ComplianceChecklistSerializer(checklist)
            return Response(serializer.data)
        except ComplianceChecklist.DoesNotExist:
            return Response({'error': 'Compliance checklist not found'}, status=status.HTTP_404_NOT_FOUND)


class DSPTComplianceReportView(APIView):
    """Generate DSPT compliance reports."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Generate DSPT compliance report."""
        return Response({'message': 'DSPT report generation not yet implemented'})


class AuditTrailReportView(APIView):
    """Generate audit trail reports."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Generate audit trail report."""
        return Response({'message': 'Audit trail report generation not yet implemented'})


class SafetyIncidentReportView(APIView):
    """Generate safety incident reports."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Generate safety incident report."""
        return Response({'message': 'Safety incident report generation not yet implemented'})


class ComplianceStatusView(APIView):
    """Get overall compliance status."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get compliance status."""
        return Response({'message': 'Compliance status monitoring not yet implemented'})


class ComplianceAlertsView(APIView):
    """Get compliance alerts and warnings."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get compliance alerts."""
        return Response({'message': 'Compliance alerts not yet implemented'})
