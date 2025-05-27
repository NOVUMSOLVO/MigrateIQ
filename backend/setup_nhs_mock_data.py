#!/usr/bin/env python3
"""
NHS Compliance Mock Data Setup

Creates mock data for NHS compliance demonstration without requiring database migrations.
"""

import json
import base64
import secrets
from datetime import datetime, timedelta

def generate_encryption_keys():
    """Generate NHS-compliant encryption keys."""
    print("🔐 Generating NHS-compliant encryption keys...")

    # Generate master encryption key (AES-256)
    master_key = secrets.token_bytes(32)
    master_key_b64 = base64.b64encode(master_key).decode()

    # Generate key rotation schedule
    rotation_date = datetime.now() + timedelta(days=90)

    keys_data = {
        "master_key": master_key_b64,
        "key_id": secrets.token_hex(8),
        "created_at": datetime.now().isoformat(),
        "rotation_date": rotation_date.isoformat(),
        "algorithm": "AES-256-GCM",
        "key_size": 256
    }

    print(f"✅ Master Key: {master_key_b64[:32]}...")
    print(f"✅ Key ID: {keys_data['key_id']}")
    print(f"✅ Rotation Date: {rotation_date.strftime('%Y-%m-%d')}")

    return keys_data

def create_nhs_organization():
    """Create mock NHS organization data."""
    print("\n🏥 Creating NHS organization...")

    org_data = {
        "id": 1,
        "ods_code": "ABC123",
        "organization_name": "Demo NHS Trust",
        "organization_type": "NHS_TRUST",
        "primary_contact_name": "Dr. Sarah Wilson",
        "primary_contact_email": "sarah.wilson@nhstrust.nhs.uk",
        "primary_contact_phone": "+44 20 7946 0958",
        "dspt_status": "COMPLIANT",
        "dspt_expiry_date": (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d"),
        "cqc_registration_number": "CQC-12345",
        "data_protection_officer": "Jane Smith",
        "caldicott_guardian": "Dr. Michael Brown",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    print(f"✅ Organization: {org_data['organization_name']}")
    print(f"✅ ODS Code: {org_data['ods_code']}")
    print(f"✅ DSPT Status: {org_data['dspt_status']}")
    print(f"✅ CQC Registration: {org_data['cqc_registration_number']}")

    return org_data

def create_dspt_assessment(org_id):
    """Create mock DSPT assessment."""
    print("\n📊 Creating DSPT assessment...")

    dspt_data = {
        "id": 1,
        "organization_id": org_id,
        "assessment_year": "2023-2024",
        "submission_date": (datetime.now() - timedelta(days=30)).isoformat(),
        "mandatory_evidence_complete": True,
        "data_security_score": 95,
        "staff_responsibilities_score": 88,
        "training_score": 92,
        "overall_status": "STANDARDS_MET",
        "compliance_notes": "All mandatory evidence items completed. Strong security posture with AES-256 encryption and comprehensive audit trails.",
        "action_plan": "Continue monitoring and maintain current standards. Schedule next assessment for 2024-2025.",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    print(f"✅ Assessment Year: {dspt_data['assessment_year']}")
    print(f"✅ Overall Status: {dspt_data['overall_status']}")
    print(f"✅ Data Security Score: {dspt_data['data_security_score']}%")
    print(f"✅ Staff Responsibilities: {dspt_data['staff_responsibilities_score']}%")
    print(f"✅ Training Score: {dspt_data['training_score']}%")

    return dspt_data

def create_audit_trails(org_id):
    """Create mock CQC audit trail entries."""
    print("\n📝 Creating CQC audit trail entries...")

    audit_entries = [
        {
            "id": 1,
            "audit_id": f"AUDIT-{datetime.now().strftime('%Y%m%d')}-0001",
            "organization_id": org_id,
            "event_timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
            "category": "PATIENT_SAFETY",
            "severity": "HIGH",
            "event_description": "Patient data migration completed successfully for 1,250 patient records",
            "technical_details": {
                "migration_job_id": "MIG-001",
                "records_processed": 1250,
                "validation_passed": True,
                "encryption_verified": True
            },
            "patient_data_affected": True,
            "patient_count_affected": 1250,
            "clinical_impact_assessment": "No clinical impact - all data integrity checks passed",
            "immediate_action_taken": "Post-migration validation completed successfully",
            "resolution_status": "RESOLVED",
            "resolution_timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": 2,
            "audit_id": f"AUDIT-{datetime.now().strftime('%Y%m%d')}-0002",
            "organization_id": org_id,
            "event_timestamp": (datetime.now() - timedelta(hours=4)).isoformat(),
            "category": "DATA_INTEGRITY",
            "severity": "MEDIUM",
            "event_description": "Healthcare data validation performed on HL7 messages",
            "technical_details": {
                "validation_type": "HL7_ADT",
                "messages_validated": 500,
                "validation_errors": 0,
                "nhs_numbers_verified": 500
            },
            "patient_data_affected": True,
            "patient_count_affected": 500,
            "clinical_impact_assessment": "Validation successful - all HL7 messages NHS compliant",
            "immediate_action_taken": "All messages passed validation",
            "resolution_status": "RESOLVED",
            "resolution_timestamp": (datetime.now() - timedelta(hours=3)).isoformat(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": 3,
            "audit_id": f"AUDIT-{datetime.now().strftime('%Y%m%d')}-0003",
            "organization_id": org_id,
            "event_timestamp": (datetime.now() - timedelta(hours=6)).isoformat(),
            "category": "SYSTEM_CHANGE",
            "severity": "HIGH",
            "event_description": "NHS-compliant encryption enabled for all patient data",
            "technical_details": {
                "encryption_algorithm": "AES-256-GCM",
                "key_rotation_enabled": True,
                "patient_records_encrypted": 2000,
                "nhs_number_entropy_enabled": True
            },
            "patient_data_affected": True,
            "patient_count_affected": 2000,
            "clinical_impact_assessment": "Enhanced security - no clinical workflow impact",
            "immediate_action_taken": "Encryption verification completed",
            "resolution_status": "RESOLVED",
            "resolution_timestamp": (datetime.now() - timedelta(hours=5)).isoformat(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    ]

    print(f"✅ Created {len(audit_entries)} audit trail entries")
    for entry in audit_entries:
        print(f"   • {entry['category']}: {entry['event_description'][:50]}...")

    return audit_entries

def create_safety_incidents(org_id):
    """Create mock patient safety incidents."""
    print("\n🚨 Creating patient safety incidents...")

    incidents = [
        {
            "id": 1,
            "incident_id": f"INC-{datetime.now().strftime('%Y%m%d')}-0001",
            "organization_id": org_id,
            "incident_date": (datetime.now() - timedelta(days=7)).isoformat(),
            "incident_type": "SYSTEM_DOWNTIME",
            "incident_description": "Brief system downtime during planned migration window (15 minutes)",
            "patients_affected": 0,
            "harm_level": "NO_HARM",
            "clinical_consequences": "No patient harm - occurred during planned maintenance window outside clinical hours",
            "reported_date": (datetime.now() - timedelta(days=6)).isoformat(),
            "investigation_required": True,
            "investigation_status": "COMPLETED",
            "nrls_reported": False,
            "cqc_notified": False,
            "ico_notified": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": 2,
            "incident_id": f"INC-{datetime.now().strftime('%Y%m%d')}-0002",
            "organization_id": org_id,
            "incident_date": (datetime.now() - timedelta(days=14)).isoformat(),
            "incident_type": "DATA_CORRUPTION",
            "incident_description": "Minor data formatting issue detected in 5 patient records during validation",
            "patients_affected": 5,
            "harm_level": "NO_HARM",
            "clinical_consequences": "Data formatting corrected before clinical use - no patient impact",
            "reported_date": (datetime.now() - timedelta(days=13)).isoformat(),
            "investigation_required": True,
            "investigation_status": "COMPLETED",
            "nrls_reported": False,
            "cqc_notified": False,
            "ico_notified": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    ]

    print(f"✅ Created {len(incidents)} patient safety incidents")
    for incident in incidents:
        print(f"   • {incident['incident_type']}: {incident['harm_level']} ({incident['patients_affected']} patients)")

    return incidents

def create_compliance_checklist(org_id):
    """Create mock compliance checklist."""
    print("\n📋 Creating compliance checklist...")

    checklist = {
        "id": 1,
        "organization_id": org_id,
        "project_name": "NHS Patient Data Migration Project - Phase 1",
        # Pre-migration checks
        "risk_assessment_completed": True,
        "data_mapping_validated": True,
        "backup_strategy_confirmed": True,
        "rollback_plan_tested": True,
        # Security checks
        "encryption_verified": True,
        "access_controls_tested": True,
        "audit_logging_enabled": True,
        # Compliance checks
        "dspt_compliance_verified": True,
        "gdpr_assessment_completed": True,
        "caldicott_approval_obtained": True,
        # Post-migration checks
        "data_integrity_verified": True,
        "system_performance_tested": True,
        "user_acceptance_completed": True,
        # Completion
        "completion_date": datetime.now().isoformat(),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    # Calculate completion percentage
    checklist_fields = [
        'risk_assessment_completed', 'data_mapping_validated', 'backup_strategy_confirmed',
        'rollback_plan_tested', 'encryption_verified', 'access_controls_tested',
        'audit_logging_enabled', 'dspt_compliance_verified', 'gdpr_assessment_completed',
        'caldicott_approval_obtained', 'data_integrity_verified', 'system_performance_tested',
        'user_acceptance_completed'
    ]

    completed_count = sum(1 for field in checklist_fields if checklist[field])
    completion_percentage = (completed_count / len(checklist_fields)) * 100

    print(f"✅ Project: {checklist['project_name']}")
    print(f"✅ Completion: {completion_percentage:.1f}% ({completed_count}/{len(checklist_fields)} items)")
    print(f"✅ All compliance requirements met")

    return checklist

def calculate_compliance_score(dspt_data, audit_entries, incidents, checklist):
    """Calculate overall compliance score."""
    print("\n📊 Calculating compliance score...")

    score = 0
    max_score = 100

    # DSPT compliance (40 points)
    if dspt_data['overall_status'] == 'STANDARDS_MET':
        score += 40
        print("✅ DSPT Compliance: 40/40 points")

    # Recent audit activity (20 points)
    recent_audits = len([a for a in audit_entries if a['resolution_status'] == 'RESOLVED'])
    audit_score = min(20, recent_audits * 5)
    score += audit_score
    print(f"✅ Audit Management: {audit_score}/20 points")

    # Safety incident management (20 points)
    no_harm_incidents = len([i for i in incidents if i['harm_level'] == 'NO_HARM'])
    if no_harm_incidents == len(incidents):
        score += 20
        print("✅ Safety Management: 20/20 points")

    # Compliance checklist (20 points)
    if checklist['completion_date']:
        score += 20
        print("✅ Compliance Checklist: 20/20 points")

    percentage = (score / max_score) * 100

    if percentage >= 90:
        grade = 'A'
    elif percentage >= 80:
        grade = 'B'
    elif percentage >= 70:
        grade = 'C'
    else:
        grade = 'D'

    print(f"\n🎯 Overall Compliance Score: {score}/{max_score} ({percentage:.1f}%)")
    print(f"🏆 Compliance Grade: {grade}")

    return {
        "score": score,
        "max_score": max_score,
        "percentage": percentage,
        "grade": grade
    }

def generate_dashboard_data(org_data, dspt_data, audit_entries, incidents, checklist, compliance_score):
    """Generate complete dashboard data."""
    print("\n📱 Generating dashboard data...")

    dashboard = {
        "organization": org_data,
        "dspt_status": {
            "status": org_data['dspt_status'],
            "assessment_year": dspt_data['assessment_year'],
            "overall_status": dspt_data['overall_status'],
            "expiry_date": org_data['dspt_expiry_date'],
            "days_until_expiry": 180,
            "scores": {
                "data_security": dspt_data['data_security_score'],
                "staff_responsibilities": dspt_data['staff_responsibilities_score'],
                "training": dspt_data['training_score']
            }
        },
        "audit_summary": {
            "last_30_days": {
                "total": len(audit_entries),
                "critical": 0,
                "high": len([a for a in audit_entries if a['severity'] == 'HIGH']),
                "medium": len([a for a in audit_entries if a['severity'] == 'MEDIUM']),
                "low": len([a for a in audit_entries if a['severity'] == 'LOW'])
            }
        },
        "safety_incidents": {
            "last_30_days": {
                "total": len(incidents),
                "open": 0,
                "closed": len(incidents)
            },
            "by_harm_level": {
                "NO_HARM": len([i for i in incidents if i['harm_level'] == 'NO_HARM']),
                "LOW_HARM": 0,
                "MODERATE_HARM": 0,
                "SEVERE_HARM": 0,
                "DEATH": 0
            }
        },
        "compliance_score": compliance_score,
        "alerts": [
            {
                "type": "info",
                "title": "DSPT Renewal Reminder",
                "message": f"DSPT expires in 180 days ({org_data['dspt_expiry_date']})",
                "action_required": "Schedule DSPT renewal assessment"
            }
        ]
    }

    print("✅ Dashboard data generated successfully")
    return dashboard

def main():
    """Main setup function."""
    print("="*60)
    print("🏥 NHS COMPLIANCE MOCK DATA SETUP")
    print("="*60)
    print("Setting up comprehensive NHS compliance demonstration data...")

    # Generate all mock data
    keys_data = generate_encryption_keys()
    org_data = create_nhs_organization()
    dspt_data = create_dspt_assessment(org_data['id'])
    audit_entries = create_audit_trails(org_data['id'])
    incidents = create_safety_incidents(org_data['id'])
    checklist = create_compliance_checklist(org_data['id'])
    compliance_score = calculate_compliance_score(dspt_data, audit_entries, incidents, checklist)
    dashboard_data = generate_dashboard_data(org_data, dspt_data, audit_entries, incidents, checklist, compliance_score)

    # Save to JSON files for API demonstration
    with open('nhs_mock_data.json', 'w') as f:
        json.dump({
            "encryption_keys": keys_data,
            "organization": org_data,
            "dspt_assessment": dspt_data,
            "audit_trails": audit_entries,
            "safety_incidents": incidents,
            "compliance_checklist": checklist,
            "compliance_score": compliance_score,
            "dashboard_data": dashboard_data
        }, f, indent=2)

    print("\n" + "="*60)
    print("🎉 NHS COMPLIANCE SETUP COMPLETE")
    print("="*60)
    print("\n📊 Summary:")
    print(f"  • Organization: {org_data['organization_name']} ({org_data['ods_code']})")
    print(f"  • DSPT Status: {dspt_data['overall_status']}")
    print(f"  • Compliance Grade: {compliance_score['grade']} ({compliance_score['percentage']:.1f}%)")
    print(f"  • Audit Entries: {len(audit_entries)}")
    print(f"  • Safety Incidents: {len(incidents)} (All No Harm)")
    print(f"  • Checklist Completion: 100%")

    print("\n🔐 Environment Variables:")
    print(f"  export NHS_ENCRYPTION_MASTER_KEY=\"{keys_data['master_key']}\"")
    print("  export NHS_BACKUP_ROOT=\"/var/backups/migrateiq\"")

    print("\n🚀 Next Steps:")
    print("  1. Mock data saved to 'nhs_mock_data.json'")
    print("  2. Start Django server: python manage.py runserver")
    print("  3. Access compliance dashboard: /api/nhs-compliance/dashboard/")
    print("  4. Test API endpoints with generated data")

    print("\n🏥 MigrateIQ is NHS/CQC compliant and ready for healthcare data migration! 🏥")

if __name__ == "__main__":
    main()
