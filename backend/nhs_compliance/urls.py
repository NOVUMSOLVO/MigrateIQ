"""
NHS Compliance URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for viewsets
router = DefaultRouter()

app_name = 'nhs_compliance'

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Dashboard and overview
    path('dashboard/', views.NHSComplianceDashboardView.as_view(), name='dashboard'),
    
    # DSPT Assessment endpoints
    path('dspt/', views.DSPTAssessmentView.as_view(), name='dspt-list'),
    path('dspt/<int:pk>/', views.DSPTAssessmentView.as_view(), name='dspt-detail'),
    
    # Healthcare data validation
    path('validate/', views.validate_healthcare_data, name='validate-healthcare-data'),
    
    # Patient data encryption
    path('encrypt/', views.encrypt_patient_data, name='encrypt-patient-data'),
    
    # Audit trails
    path('audit/', views.CQCAuditTrailListView.as_view(), name='audit-list'),
    path('audit/<uuid:audit_id>/', views.CQCAuditTrailDetailView.as_view(), name='audit-detail'),
    
    # Safety incidents
    path('incidents/', views.PatientSafetyIncidentListView.as_view(), name='incidents-list'),
    path('incidents/<uuid:incident_id>/', views.PatientSafetyIncidentDetailView.as_view(), name='incidents-detail'),
    
    # Compliance checklists
    path('checklists/', views.ComplianceChecklistListView.as_view(), name='checklists-list'),
    path('checklists/<int:pk>/', views.ComplianceChecklistDetailView.as_view(), name='checklists-detail'),
    
    # Reports and exports
    path('reports/dspt/', views.DSPTComplianceReportView.as_view(), name='dspt-report'),
    path('reports/audit/', views.AuditTrailReportView.as_view(), name='audit-report'),
    path('reports/incidents/', views.SafetyIncidentReportView.as_view(), name='incidents-report'),
    
    # Compliance monitoring
    path('monitoring/status/', views.ComplianceStatusView.as_view(), name='compliance-status'),
    path('monitoring/alerts/', views.ComplianceAlertsView.as_view(), name='compliance-alerts'),
]
