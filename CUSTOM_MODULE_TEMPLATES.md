# MigrateIQ Custom Module Development Templates

## 🏗️ **BACKEND MODULE TEMPLATE**

### **1. Healthcare Extension Module Example**

#### **Module Structure**
```
backend/healthcare_extensions/
├── __init__.py
├── apps.py
├── models.py
├── views.py
├── serializers.py
├── urls.py
├── services.py
├── tasks.py
├── validators.py
└── tests.py
```

#### **models.py - Healthcare Data Models**
```python
from django.db import models
from django.contrib.auth import get_user_model
from core.models import Tenant, TimeStampedModel

User = get_user_model()

class Patient(TimeStampedModel):
    """Patient data model for healthcare migrations."""
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    
    # Patient identifiers
    nhs_number = models.CharField(max_length=10, unique=True)
    hospital_number = models.CharField(max_length=20)
    
    # Demographics
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])
    
    # Contact information
    address = models.TextField()
    postcode = models.CharField(max_length=10)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    # Clinical information
    gp_practice = models.CharField(max_length=100)
    allergies = models.TextField(blank=True)
    medical_conditions = models.JSONField(default=list)
    
    # Data migration tracking
    source_system = models.CharField(max_length=100)
    migration_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('IN_PROGRESS', 'In Progress'),
            ('COMPLETED', 'Completed'),
            ('FAILED', 'Failed'),
        ],
        default='PENDING'
    )
    
    class Meta:
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'
        indexes = [
            models.Index(fields=['nhs_number']),
            models.Index(fields=['tenant', 'migration_status']),
        ]

class ClinicalRecord(TimeStampedModel):
    """Clinical record for patient encounters."""
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='clinical_records')
    
    # Record details
    record_type = models.CharField(
        max_length=20,
        choices=[
            ('CONSULTATION', 'Consultation'),
            ('ADMISSION', 'Admission'),
            ('DISCHARGE', 'Discharge'),
            ('PROCEDURE', 'Procedure'),
            ('MEDICATION', 'Medication'),
        ]
    )
    
    encounter_date = models.DateTimeField()
    clinician = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    
    # Clinical data
    diagnosis_codes = models.JSONField(default=list)  # ICD-10 codes
    procedure_codes = models.JSONField(default=list)  # OPCS-4 codes
    medications = models.JSONField(default=list)
    
    # Free text
    clinical_notes = models.TextField()
    
    # Data quality
    data_quality_score = models.FloatField(default=0.0)
    validation_errors = models.JSONField(default=list)
    
    class Meta:
        verbose_name = 'Clinical Record'
        verbose_name_plural = 'Clinical Records'
        indexes = [
            models.Index(fields=['patient', 'encounter_date']),
            models.Index(fields=['record_type', 'encounter_date']),
        ]
```

#### **services.py - Healthcare Business Logic**
```python
import re
from typing import Dict, List, Optional
from django.db import transaction
from .models import Patient, ClinicalRecord
from .validators import NHSNumberValidator, ICD10Validator

class HealthcareDataService:
    """Service for healthcare-specific data operations."""
    
    def __init__(self):
        self.nhs_validator = NHSNumberValidator()
        self.icd10_validator = ICD10Validator()
    
    @transaction.atomic
    def migrate_patient_data(self, source_data: Dict) -> Patient:
        """Migrate patient data with healthcare-specific validation."""
        
        # Validate NHS number
        nhs_number = source_data.get('nhs_number')
        if not self.nhs_validator.is_valid(nhs_number):
            raise ValueError(f"Invalid NHS number: {nhs_number}")
        
        # Create patient record
        patient = Patient.objects.create(
            nhs_number=nhs_number,
            hospital_number=source_data.get('hospital_number'),
            first_name=source_data.get('first_name'),
            last_name=source_data.get('last_name'),
            date_of_birth=source_data.get('date_of_birth'),
            gender=source_data.get('gender'),
            address=source_data.get('address'),
            postcode=source_data.get('postcode'),
            phone=source_data.get('phone', ''),
            email=source_data.get('email', ''),
            gp_practice=source_data.get('gp_practice'),
            allergies=source_data.get('allergies', ''),
            medical_conditions=source_data.get('medical_conditions', []),
            source_system=source_data.get('source_system'),
        )
        
        # Migrate clinical records
        clinical_records = source_data.get('clinical_records', [])
        for record_data in clinical_records:
            self.migrate_clinical_record(patient, record_data)
        
        return patient
    
    def migrate_clinical_record(self, patient: Patient, record_data: Dict) -> ClinicalRecord:
        """Migrate clinical record with validation."""
        
        # Validate diagnosis codes
        diagnosis_codes = record_data.get('diagnosis_codes', [])
        validated_codes = []
        validation_errors = []
        
        for code in diagnosis_codes:
            if self.icd10_validator.is_valid(code):
                validated_codes.append(code)
            else:
                validation_errors.append(f"Invalid ICD-10 code: {code}")
        
        # Calculate data quality score
        quality_score = self.calculate_data_quality(record_data, validation_errors)
        
        return ClinicalRecord.objects.create(
            patient=patient,
            record_type=record_data.get('record_type'),
            encounter_date=record_data.get('encounter_date'),
            clinician=record_data.get('clinician'),
            department=record_data.get('department'),
            diagnosis_codes=validated_codes,
            procedure_codes=record_data.get('procedure_codes', []),
            medications=record_data.get('medications', []),
            clinical_notes=record_data.get('clinical_notes', ''),
            data_quality_score=quality_score,
            validation_errors=validation_errors,
        )
    
    def calculate_data_quality(self, record_data: Dict, validation_errors: List) -> float:
        """Calculate data quality score for clinical record."""
        
        total_fields = len(record_data)
        empty_fields = sum(1 for value in record_data.values() if not value)
        error_count = len(validation_errors)
        
        # Quality score based on completeness and validation
        completeness_score = (total_fields - empty_fields) / total_fields
        validation_score = max(0, 1 - (error_count / total_fields))
        
        return (completeness_score + validation_score) / 2

class PatientDataAnonymizer:
    """Service for anonymizing patient data for research/testing."""
    
    def anonymize_patient(self, patient: Patient) -> Dict:
        """Anonymize patient data while preserving clinical value."""
        
        return {
            'patient_id': f"ANON_{patient.id}",
            'age_group': self.get_age_group(patient.date_of_birth),
            'gender': patient.gender,
            'postcode_area': patient.postcode[:2] if patient.postcode else '',
            'medical_conditions': patient.medical_conditions,
            'clinical_records_count': patient.clinical_records.count(),
        }
    
    def get_age_group(self, date_of_birth) -> str:
        """Convert date of birth to age group."""
        from datetime import date
        
        age = (date.today() - date_of_birth).days // 365
        
        if age < 18:
            return "0-17"
        elif age < 30:
            return "18-29"
        elif age < 50:
            return "30-49"
        elif age < 70:
            return "50-69"
        else:
            return "70+"
```

#### **views.py - Healthcare API Endpoints**
```python
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .models import Patient, ClinicalRecord
from .serializers import PatientSerializer, ClinicalRecordSerializer
from .services import HealthcareDataService, PatientDataAnonymizer

class PatientViewSet(viewsets.ModelViewSet):
    """API endpoints for patient management."""
    
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter patients by tenant."""
        return Patient.objects.filter(tenant=self.request.user.tenant)
    
    @extend_schema(
        summary="Migrate patient data",
        description="Migrate patient data from source system with healthcare validation"
    )
    @action(detail=False, methods=['post'])
    def migrate(self, request):
        """Migrate patient data from source system."""
        
        service = HealthcareDataService()
        
        try:
            patient = service.migrate_patient_data(request.data)
            serializer = self.get_serializer(patient)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        summary="Anonymize patient data",
        description="Generate anonymized patient data for research/testing"
    )
    @action(detail=True, methods=['post'])
    def anonymize(self, request, pk=None):
        """Anonymize patient data."""
        
        patient = self.get_object()
        anonymizer = PatientDataAnonymizer()
        
        anonymized_data = anonymizer.anonymize_patient(patient)
        
        return Response(anonymized_data)
    
    @extend_schema(
        summary="Get data quality report",
        description="Generate data quality report for patient records"
    )
    @action(detail=True, methods=['get'])
    def data_quality(self, request, pk=None):
        """Get data quality report for patient."""
        
        patient = self.get_object()
        records = patient.clinical_records.all()
        
        quality_report = {
            'patient_id': patient.id,
            'total_records': records.count(),
            'average_quality_score': records.aggregate(
                avg_score=models.Avg('data_quality_score')
            )['avg_score'] or 0,
            'records_with_errors': records.filter(
                validation_errors__len__gt=0
            ).count(),
            'quality_by_record_type': {},
        }
        
        # Quality by record type
        for record_type, _ in ClinicalRecord._meta.get_field('record_type').choices:
            type_records = records.filter(record_type=record_type)
            if type_records.exists():
                quality_report['quality_by_record_type'][record_type] = {
                    'count': type_records.count(),
                    'average_quality': type_records.aggregate(
                        avg_score=models.Avg('data_quality_score')
                    )['avg_score'] or 0,
                }
        
        return Response(quality_report)
```

---

## 🎨 **FRONTEND COMPONENT TEMPLATE**

### **Healthcare Dashboard Component**

#### **HealthcareDashboard.js**
```javascript
import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  LinearProgress,
  Alert,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material';
import {
  LocalHospital as HospitalIcon,
  Person as PersonIcon,
  Assessment as AssessmentIcon,
  Security as SecurityIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material';
import { Line, Doughnut } from 'react-chartjs-2';
import api from '../../services/api';

const HealthcareDashboard = () => {
  const [dashboardData, setDashboardData] = useState({
    patients: {
      total: 0,
      migrated: 0,
      pending: 0,
      failed: 0,
    },
    dataQuality: {
      averageScore: 0,
      recordsWithErrors: 0,
      qualityTrend: [],
    },
    compliance: {
      nhsCompliant: true,
      gdprCompliant: true,
      lastAudit: null,
      issues: [],
    },
  });
  
  const [loading, setLoading] = useState(true);
  const [complianceDialogOpen, setComplianceDialogOpen] = useState(false);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch patient statistics
      const patientsResponse = await api.get('/healthcare/patients/statistics/');
      
      // Fetch data quality metrics
      const qualityResponse = await api.get('/healthcare/data-quality/summary/');
      
      // Fetch compliance status
      const complianceResponse = await api.get('/healthcare/compliance/status/');
      
      setDashboardData({
        patients: patientsResponse.data,
        dataQuality: qualityResponse.data,
        compliance: complianceResponse.data,
      });
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getQualityColor = (score) => {
    if (score >= 0.9) return 'success';
    if (score >= 0.7) return 'warning';
    return 'error';
  };

  const qualityChartData = {
    labels: ['Excellent (90-100%)', 'Good (70-89%)', 'Poor (<70%)'],
    datasets: [{
      data: [
        dashboardData.dataQuality.excellent || 0,
        dashboardData.dataQuality.good || 0,
        dashboardData.dataQuality.poor || 0,
      ],
      backgroundColor: ['#4caf50', '#ff9800', '#f44336'],
    }],
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2 }}>Loading healthcare dashboard...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Healthcare Migration Dashboard
      </Typography>

      {/* Patient Statistics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <PersonIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Total Patients</Typography>
              </Box>
              <Typography variant="h3" color="primary">
                {dashboardData.patients.total.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <CheckIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="h6">Migrated</Typography>
              </Box>
              <Typography variant="h3" color="success.main">
                {dashboardData.patients.migrated.toLocaleString()}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={(dashboardData.patients.migrated / dashboardData.patients.total) * 100}
                color="success"
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <AssessmentIcon color="info" sx={{ mr: 1 }} />
                <Typography variant="h6">Data Quality</Typography>
              </Box>
              <Typography variant="h3" color="info.main">
                {(dashboardData.dataQuality.averageScore * 100).toFixed(1)}%
              </Typography>
              <Chip
                label={getQualityColor(dashboardData.dataQuality.averageScore)}
                color={getQualityColor(dashboardData.dataQuality.averageScore)}
                size="small"
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <SecurityIcon color="secondary" sx={{ mr: 1 }} />
                <Typography variant="h6">Compliance</Typography>
              </Box>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip
                  label="NHS"
                  color={dashboardData.compliance.nhsCompliant ? 'success' : 'error'}
                  size="small"
                />
                <Chip
                  label="GDPR"
                  color={dashboardData.compliance.gdprCompliant ? 'success' : 'error'}
                  size="small"
                />
              </Box>
              <Button
                size="small"
                onClick={() => setComplianceDialogOpen(true)}
                sx={{ mt: 1 }}
              >
                View Details
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Data Quality Chart */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Data Quality Distribution
              </Typography>
              <Box sx={{ height: 300, display: 'flex', justifyContent: 'center' }}>
                <Doughnut data={qualityChartData} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Migration Progress
              </Typography>
              {/* Migration progress chart would go here */}
              <Typography variant="body2" color="textSecondary">
                Migration progress visualization will be implemented here.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Compliance Dialog */}
      <Dialog
        open={complianceDialogOpen}
        onClose={() => setComplianceDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Compliance Status Details</DialogTitle>
        <DialogContent>
          <List>
            <ListItem>
              <ListItemIcon>
                <HospitalIcon color="primary" />
              </ListItemIcon>
              <ListItemText
                primary="NHS Compliance"
                secondary={dashboardData.compliance.nhsCompliant ? 'Compliant' : 'Non-compliant'}
              />
              <Chip
                color={dashboardData.compliance.nhsCompliant ? 'success' : 'error'}
                label={dashboardData.compliance.nhsCompliant ? 'PASS' : 'FAIL'}
              />
            </ListItem>
            
            <ListItem>
              <ListItemIcon>
                <SecurityIcon color="primary" />
              </ListItemIcon>
              <ListItemText
                primary="GDPR Compliance"
                secondary={dashboardData.compliance.gdprCompliant ? 'Compliant' : 'Non-compliant'}
              />
              <Chip
                color={dashboardData.compliance.gdprCompliant ? 'success' : 'error'}
                label={dashboardData.compliance.gdprCompliant ? 'PASS' : 'FAIL'}
              />
            </ListItem>
          </List>

          {dashboardData.compliance.issues.length > 0 && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              <Typography variant="subtitle2">Compliance Issues:</Typography>
              <ul>
                {dashboardData.compliance.issues.map((issue, index) => (
                  <li key={index}>{issue}</li>
                ))}
              </ul>
            </Alert>
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default HealthcareDashboard;
```

---

## 🧪 **TESTING TEMPLATES**

### **Backend Tests**
```python
# tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Patient, ClinicalRecord
from .services import HealthcareDataService

User = get_user_model()

class HealthcareDataServiceTest(TestCase):
    def setUp(self):
        self.service = HealthcareDataService()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_migrate_patient_data(self):
        """Test patient data migration with validation."""
        patient_data = {
            'nhs_number': '9434765919',  # Valid NHS number
            'hospital_number': 'H123456',
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': '1980-01-01',
            'gender': 'M',
            'source_system': 'Legacy System',
        }
        
        patient = self.service.migrate_patient_data(patient_data)
        
        self.assertEqual(patient.nhs_number, '9434765919')
        self.assertEqual(patient.first_name, 'John')
        self.assertEqual(patient.migration_status, 'PENDING')
```

### **Frontend Tests**
```javascript
// HealthcareDashboard.test.js
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import HealthcareDashboard from './HealthcareDashboard';
import api from '../../services/api';

jest.mock('../../services/api');

const theme = createTheme();

const renderWithTheme = (component) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('HealthcareDashboard', () => {
  beforeEach(() => {
    api.get.mockClear();
  });

  test('renders dashboard with patient statistics', async () => {
    const mockData = {
      patients: { total: 1000, migrated: 800, pending: 150, failed: 50 },
      dataQuality: { averageScore: 0.85, recordsWithErrors: 25 },
      compliance: { nhsCompliant: true, gdprCompliant: true },
    };

    api.get.mockResolvedValue({ data: mockData.patients });

    renderWithTheme(<HealthcareDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Healthcare Migration Dashboard')).toBeInTheDocument();
      expect(screen.getByText('1,000')).toBeInTheDocument();
    });
  });
});
```

This comprehensive template system provides the foundation for building industry-specific customizations and advanced features for MigrateIQ. Each template can be adapted for different industries and use cases.
