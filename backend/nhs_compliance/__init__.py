"""
NHS Compliance Module for MigrateIQ

This module provides NHS and CQC compliance features for healthcare data migration,
ensuring adherence to UK healthcare regulations and standards.
"""

__version__ = '1.0.0'
__author__ = 'MigrateIQ Team'

# NHS Compliance feature flags
NHS_COMPLIANCE_FEATURES = {
    'DSPT_COMPLIANCE': True,
    'CQC_AUDIT_TRAILS': True,
    'PATIENT_SAFETY_VALIDATION': True,
    'HEALTHCARE_STANDARDS': True,
    'NHS_ENCRYPTION': True,
    'DATA_ANONYMIZATION': True,
    'DISASTER_RECOVERY': True,
}

# NHS Data Security and Protection Toolkit requirements
DSPT_REQUIREMENTS = {
    'ENCRYPTION_AT_REST': 'AES-256',
    'ENCRYPTION_IN_TRANSIT': 'TLS 1.3',
    'ACCESS_CONTROL': 'RBAC with MFA',
    'AUDIT_RETENTION': '7_YEARS',
    'INCIDENT_RESPONSE': 'AUTOMATED',
    'BACKUP_FREQUENCY': 'DAILY',
    'RECOVERY_TIME_OBJECTIVE': '4_HOURS',
    'RECOVERY_POINT_OBJECTIVE': '1_HOUR',
}

# CQC Key Lines of Enquiry compliance
CQC_KLOE_COMPLIANCE = {
    'SAFETY': {
        'patient_data_integrity': True,
        'migration_risk_assessment': True,
        'rollback_capability': True,
    },
    'EFFECTIVENESS': {
        'data_quality_validation': True,
        'clinical_workflow_continuity': True,
        'performance_monitoring': True,
    },
    'GOVERNANCE': {
        'regulatory_compliance': True,
        'audit_trails': True,
        'staff_training_records': True,
    },
}
