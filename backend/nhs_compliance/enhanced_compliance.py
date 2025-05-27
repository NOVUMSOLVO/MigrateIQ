"""
Enhanced NHS Compliance Module for MigrateIQ
Provides comprehensive healthcare data compliance features.
"""

import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from cryptography.fernet import Fernet
import re

logger = logging.getLogger(__name__)


class ComplianceLevel(Enum):
    """NHS compliance levels."""
    BASIC = "basic"
    ENHANCED = "enhanced"
    CRITICAL = "critical"


class DataClassification(Enum):
    """NHS data classification levels."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass
class ComplianceResult:
    """Result of compliance check."""
    is_compliant: bool
    level: ComplianceLevel
    issues: List[str]
    recommendations: List[str]
    score: float
    timestamp: datetime


class NHSDataValidator:
    """Enhanced NHS data validation and compliance checker."""
    
    def __init__(self):
        self.encryption_key = self._get_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
    def _get_encryption_key(self) -> bytes:
        """Get or generate encryption key for NHS data."""
        key = getattr(settings, 'NHS_ENCRYPTION_KEY', None)
        if not key:
            key = Fernet.generate_key()
            logger.warning("Generated new NHS encryption key. Store securely!")
        return key if isinstance(key, bytes) else key.encode()
    
    def validate_nhs_number(self, nhs_number: str) -> bool:
        """Validate NHS number using Modulus 11 algorithm."""
        if not nhs_number or len(nhs_number) != 10:
            return False
        
        # Remove spaces and validate format
        nhs_clean = re.sub(r'\s+', '', nhs_number)
        if not nhs_clean.isdigit():
            return False
        
        # Modulus 11 check
        total = 0
        for i, digit in enumerate(nhs_clean[:9]):
            total += int(digit) * (10 - i)
        
        remainder = total % 11
        check_digit = 11 - remainder
        
        if check_digit == 11:
            check_digit = 0
        elif check_digit == 10:
            return False  # Invalid NHS number
        
        return int(nhs_clean[9]) == check_digit
    
    def validate_chi_number(self, chi_number: str) -> bool:
        """Validate Scottish CHI (Community Health Index) number."""
        if not chi_number or len(chi_number) != 10:
            return False
        
        chi_clean = re.sub(r'\s+', '', chi_number)
        if not chi_clean.isdigit():
            return False
        
        # Basic format validation (DDMMYY followed by 4 digits)
        day = int(chi_clean[:2])
        month = int(chi_clean[2:4])
        year = int(chi_clean[4:6])
        
        if not (1 <= day <= 31 and 1 <= month <= 12):
            return False
        
        return True
    
    def validate_h_c_number(self, hc_number: str) -> bool:
        """Validate Northern Ireland H&C number."""
        if not hc_number or len(hc_number) != 10:
            return False
        
        hc_clean = re.sub(r'\s+', '', hc_number)
        return hc_clean.isdigit()
    
    def classify_data_sensitivity(self, data: Dict[str, Any]) -> DataClassification:
        """Classify data based on NHS sensitivity guidelines."""
        sensitive_fields = {
            'nhs_number', 'chi_number', 'hc_number', 'patient_id',
            'medical_record', 'diagnosis', 'treatment', 'medication',
            'mental_health', 'sexual_health', 'genetic_data'
        }
        
        confidential_fields = {
            'social_security', 'financial_data', 'insurance',
            'employment_record', 'criminal_record'
        }
        
        field_names = set(str(key).lower() for key in data.keys())
        
        if any(field in field_names for field in sensitive_fields):
            return DataClassification.RESTRICTED
        elif any(field in field_names for field in confidential_fields):
            return DataClassification.CONFIDENTIAL
        elif any('personal' in field or 'private' in field for field in field_names):
            return DataClassification.INTERNAL
        else:
            return DataClassification.PUBLIC
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive NHS data."""
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return encrypted_data.decode()
        except Exception as e:
            logger.error(f"Failed to encrypt NHS data: {e}")
            raise ValidationError("Data encryption failed")
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive NHS data."""
        try:
            decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode())
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt NHS data: {e}")
            raise ValidationError("Data decryption failed")


class DSPTComplianceChecker:
    """Data Security and Protection Toolkit compliance checker."""
    
    def __init__(self):
        self.validator = NHSDataValidator()
        
    def check_data_minimization(self, data: Dict[str, Any]) -> ComplianceResult:
        """Check if data collection follows minimization principles."""
        issues = []
        recommendations = []
        score = 100.0
        
        # Check for unnecessary fields
        unnecessary_fields = {
            'social_media', 'personal_preferences', 'marketing_data',
            'non_medical_interests', 'lifestyle_choices'
        }
        
        found_unnecessary = [
            field for field in data.keys() 
            if any(unnecessary in str(field).lower() for unnecessary in unnecessary_fields)
        ]
        
        if found_unnecessary:
            issues.append(f"Unnecessary data fields detected: {found_unnecessary}")
            recommendations.append("Remove non-essential data fields to comply with data minimization")
            score -= 20
        
        # Check data retention indicators
        if 'retention_period' not in data and 'created_date' not in data:
            issues.append("No data retention information found")
            recommendations.append("Add data retention metadata for GDPR compliance")
            score -= 15
        
        return ComplianceResult(
            is_compliant=len(issues) == 0,
            level=ComplianceLevel.ENHANCED,
            issues=issues,
            recommendations=recommendations,
            score=max(0, score),
            timestamp=timezone.now()
        )
    
    def check_access_controls(self, user_permissions: Dict[str, List[str]]) -> ComplianceResult:
        """Check access control compliance."""
        issues = []
        recommendations = []
        score = 100.0
        
        # Check for role-based access
        required_roles = {'admin', 'clinician', 'data_processor', 'viewer'}
        available_roles = set(user_permissions.keys())
        
        if not required_roles.issubset(available_roles):
            missing_roles = required_roles - available_roles
            issues.append(f"Missing required roles: {missing_roles}")
            recommendations.append("Implement comprehensive role-based access control")
            score -= 25
        
        # Check for excessive permissions
        for role, permissions in user_permissions.items():
            if role == 'viewer' and any('write' in perm or 'delete' in perm for perm in permissions):
                issues.append(f"Viewer role has excessive permissions: {permissions}")
                recommendations.append("Restrict viewer role to read-only permissions")
                score -= 15
        
        return ComplianceResult(
            is_compliant=len(issues) == 0,
            level=ComplianceLevel.CRITICAL,
            issues=issues,
            recommendations=recommendations,
            score=max(0, score),
            timestamp=timezone.now()
        )
    
    def check_audit_trail(self, audit_logs: List[Dict[str, Any]]) -> ComplianceResult:
        """Check audit trail compliance."""
        issues = []
        recommendations = []
        score = 100.0
        
        if not audit_logs:
            issues.append("No audit logs found")
            recommendations.append("Implement comprehensive audit logging")
            return ComplianceResult(
                is_compliant=False,
                level=ComplianceLevel.CRITICAL,
                issues=issues,
                recommendations=recommendations,
                score=0,
                timestamp=timezone.now()
            )
        
        required_fields = {'timestamp', 'user_id', 'action', 'resource', 'ip_address'}
        
        for i, log in enumerate(audit_logs[:10]):  # Check first 10 logs
            missing_fields = required_fields - set(log.keys())
            if missing_fields:
                issues.append(f"Audit log {i} missing fields: {missing_fields}")
                score -= 5
        
        # Check log retention
        oldest_log = min(audit_logs, key=lambda x: x.get('timestamp', datetime.min))
        if oldest_log.get('timestamp'):
            log_age = timezone.now() - oldest_log['timestamp']
            if log_age < timedelta(days=2555):  # 7 years NHS requirement
                recommendations.append("Ensure audit logs are retained for 7 years minimum")
        
        if issues:
            recommendations.append("Enhance audit logging to include all required fields")
        
        return ComplianceResult(
            is_compliant=len(issues) == 0,
            level=ComplianceLevel.CRITICAL,
            issues=issues,
            recommendations=recommendations,
            score=max(0, score),
            timestamp=timezone.now()
        )


class NHSComplianceManager:
    """Main NHS compliance management class."""
    
    def __init__(self):
        self.validator = NHSDataValidator()
        self.dspt_checker = DSPTComplianceChecker()
    
    def perform_comprehensive_check(self, 
                                  data: Dict[str, Any],
                                  user_permissions: Dict[str, List[str]],
                                  audit_logs: List[Dict[str, Any]]) -> Dict[str, ComplianceResult]:
        """Perform comprehensive NHS compliance check."""
        
        results = {
            'data_minimization': self.dspt_checker.check_data_minimization(data),
            'access_controls': self.dspt_checker.check_access_controls(user_permissions),
            'audit_trail': self.dspt_checker.check_audit_trail(audit_logs),
        }
        
        # Additional checks
        results['data_classification'] = self._check_data_classification(data)
        results['encryption'] = self._check_encryption_compliance(data)
        
        return results
    
    def _check_data_classification(self, data: Dict[str, Any]) -> ComplianceResult:
        """Check data classification compliance."""
        classification = self.validator.classify_data_sensitivity(data)
        
        issues = []
        recommendations = []
        score = 100.0
        
        if classification == DataClassification.RESTRICTED:
            if 'encryption_status' not in data or not data['encryption_status']:
                issues.append("Restricted data must be encrypted")
                recommendations.append("Implement encryption for all restricted NHS data")
                score -= 50
        
        return ComplianceResult(
            is_compliant=len(issues) == 0,
            level=ComplianceLevel.ENHANCED,
            issues=issues,
            recommendations=recommendations,
            score=max(0, score),
            timestamp=timezone.now()
        )
    
    def _check_encryption_compliance(self, data: Dict[str, Any]) -> ComplianceResult:
        """Check encryption compliance."""
        issues = []
        recommendations = []
        score = 100.0
        
        sensitive_fields = ['nhs_number', 'chi_number', 'hc_number', 'patient_id']
        
        for field in sensitive_fields:
            if field in data:
                # Check if field appears to be encrypted (basic heuristic)
                value = str(data[field])
                if len(value) < 20 or value.isdigit():  # Likely not encrypted
                    issues.append(f"Field '{field}' appears to be unencrypted")
                    score -= 20
        
        if issues:
            recommendations.append("Encrypt all sensitive NHS data fields")
            recommendations.append("Use AES-256 encryption or equivalent")
        
        return ComplianceResult(
            is_compliant=len(issues) == 0,
            level=ComplianceLevel.CRITICAL,
            issues=issues,
            recommendations=recommendations,
            score=max(0, score),
            timestamp=timezone.now()
        )
    
    def generate_compliance_report(self, results: Dict[str, ComplianceResult]) -> Dict[str, Any]:
        """Generate comprehensive compliance report."""
        overall_score = sum(result.score for result in results.values()) / len(results)
        all_compliant = all(result.is_compliant for result in results.values())
        
        all_issues = []
        all_recommendations = []
        
        for check_name, result in results.items():
            all_issues.extend([f"{check_name}: {issue}" for issue in result.issues])
            all_recommendations.extend([f"{check_name}: {rec}" for rec in result.recommendations])
        
        return {
            'overall_compliant': all_compliant,
            'overall_score': round(overall_score, 2),
            'total_checks': len(results),
            'passed_checks': sum(1 for result in results.values() if result.is_compliant),
            'failed_checks': sum(1 for result in results.values() if not result.is_compliant),
            'all_issues': all_issues,
            'all_recommendations': all_recommendations,
            'detailed_results': {name: {
                'compliant': result.is_compliant,
                'score': result.score,
                'level': result.level.value,
                'issues': result.issues,
                'recommendations': result.recommendations
            } for name, result in results.items()},
            'generated_at': timezone.now().isoformat()
        }
