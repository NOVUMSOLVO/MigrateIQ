"""
Healthcare Standards Validators

Validation functions for healthcare data standards and NHS-specific requirements.
"""

import re
import json
import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class NHSNumberValidator:
    """Validator for NHS Numbers using Modulus 11 check."""
    
    @staticmethod
    def validate(nhs_number: str) -> Tuple[bool, str]:
        """
        Validate NHS Number using Modulus 11 algorithm.
        
        Args:
            nhs_number: The NHS number to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not nhs_number:
            return False, "NHS Number is required"
        
        # Remove spaces and hyphens
        nhs_number = re.sub(r'[\s-]', '', nhs_number)
        
        # Check format
        if not re.match(r'^\d{10}$', nhs_number):
            return False, "NHS Number must be exactly 10 digits"
        
        # Calculate check digit using Modulus 11
        try:
            digits = [int(d) for d in nhs_number[:9]]
            weights = [10, 9, 8, 7, 6, 5, 4, 3, 2]
            
            total = sum(digit * weight for digit, weight in zip(digits, weights))
            remainder = total % 11
            check_digit = 11 - remainder
            
            if check_digit == 11:
                check_digit = 0
            elif check_digit == 10:
                return False, "Invalid NHS Number - check digit cannot be 10"
            
            if check_digit != int(nhs_number[9]):
                return False, "Invalid NHS Number - check digit mismatch"
            
            return True, "Valid NHS Number"
            
        except (ValueError, IndexError) as e:
            return False, f"Invalid NHS Number format: {str(e)}"


class HL7Validator:
    """Validator for HL7 messages."""
    
    SUPPORTED_VERSIONS = ['2.3', '2.4', '2.5', '2.6', '2.7', '2.8']
    REQUIRED_SEGMENTS = {
        'ADT': ['MSH', 'EVN', 'PID'],
        'ORM': ['MSH', 'PID', 'ORC', 'OBR'],
        'ORU': ['MSH', 'PID', 'OBR', 'OBX'],
    }
    
    @classmethod
    def validate_message(cls, message: str) -> Tuple[bool, List[str]]:
        """
        Validate HL7 message structure.
        
        Args:
            message: HL7 message string
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not message:
            return False, ["HL7 message is empty"]
        
        lines = message.strip().split('\n')
        if not lines:
            return False, ["No segments found in HL7 message"]
        
        # Validate MSH segment (must be first)
        msh_segment = lines[0]
        if not msh_segment.startswith('MSH'):
            errors.append("First segment must be MSH (Message Header)")
        
        # Extract message type from MSH segment
        try:
            msh_fields = msh_segment.split('|')
            if len(msh_fields) < 9:
                errors.append("MSH segment missing required fields")
            else:
                message_type = msh_fields[8].split('^')[0] if '^' in msh_fields[8] else msh_fields[8]
                
                # Validate required segments for message type
                if message_type in cls.REQUIRED_SEGMENTS:
                    required_segments = cls.REQUIRED_SEGMENTS[message_type]
                    present_segments = [line.split('|')[0] for line in lines]
                    
                    for required_segment in required_segments:
                        if required_segment not in present_segments:
                            errors.append(f"Required segment {required_segment} missing for {message_type} message")
        
        except (IndexError, ValueError) as e:
            errors.append(f"Error parsing MSH segment: {str(e)}")
        
        # Validate segment structure
        for i, line in enumerate(lines):
            if not cls._validate_segment_structure(line):
                errors.append(f"Invalid segment structure at line {i + 1}: {line[:50]}...")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_segment_structure(segment: str) -> bool:
        """Validate basic HL7 segment structure."""
        if len(segment) < 3:
            return False
        
        # Segment ID should be 3 uppercase letters
        segment_id = segment[:3]
        if not re.match(r'^[A-Z]{3}$', segment_id):
            return False
        
        # Should have field separator after segment ID
        if len(segment) > 3 and segment[3] != '|':
            return False
        
        return True


class FHIRValidator:
    """Validator for FHIR resources."""
    
    REQUIRED_FIELDS = {
        'Patient': ['resourceType', 'id'],
        'Observation': ['resourceType', 'status', 'code', 'subject'],
        'Encounter': ['resourceType', 'status', 'class', 'subject'],
        'Medication': ['resourceType', 'code'],
        'DiagnosticReport': ['resourceType', 'status', 'code', 'subject'],
    }
    
    @classmethod
    def validate_resource(cls, resource_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate FHIR resource.
        
        Args:
            resource_data: FHIR resource as dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not isinstance(resource_data, dict):
            return False, ["FHIR resource must be a JSON object"]
        
        # Check resourceType
        resource_type = resource_data.get('resourceType')
        if not resource_type:
            errors.append("Missing required field: resourceType")
        elif resource_type not in cls.REQUIRED_FIELDS:
            errors.append(f"Unsupported resource type: {resource_type}")
        else:
            # Validate required fields for this resource type
            required_fields = cls.REQUIRED_FIELDS[resource_type]
            for field in required_fields:
                if field not in resource_data:
                    errors.append(f"Missing required field: {field}")
        
        # Validate specific resource types
        if resource_type == 'Patient':
            errors.extend(cls._validate_patient(resource_data))
        elif resource_type == 'Observation':
            errors.extend(cls._validate_observation(resource_data))
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_patient(patient_data: Dict[str, Any]) -> List[str]:
        """Validate Patient resource specific fields."""
        errors = []
        
        # Validate identifiers (should include NHS Number)
        identifiers = patient_data.get('identifier', [])
        nhs_number_found = False
        
        for identifier in identifiers:
            if isinstance(identifier, dict):
                system = identifier.get('system', '')
                if 'nhs-number' in system.lower():
                    nhs_number_found = True
                    value = identifier.get('value', '')
                    is_valid, error_msg = NHSNumberValidator.validate(value)
                    if not is_valid:
                        errors.append(f"Invalid NHS Number: {error_msg}")
        
        if not nhs_number_found:
            errors.append("Patient should have NHS Number identifier")
        
        return errors
    
    @staticmethod
    def _validate_observation(observation_data: Dict[str, Any]) -> List[str]:
        """Validate Observation resource specific fields."""
        errors = []
        
        # Validate status
        status = observation_data.get('status')
        valid_statuses = ['registered', 'preliminary', 'final', 'amended', 'corrected', 'cancelled', 'entered-in-error', 'unknown']
        if status not in valid_statuses:
            errors.append(f"Invalid observation status: {status}")
        
        # Validate code (should have coding)
        code = observation_data.get('code', {})
        if not code.get('coding'):
            errors.append("Observation code must have coding")
        
        return errors


class DICOMValidator:
    """Validator for DICOM data elements."""
    
    REQUIRED_TAGS = {
        'Patient': ['0010,0010', '0010,0020'],  # Patient Name, Patient ID
        'Study': ['0020,000D', '0020,0010'],    # Study Instance UID, Study ID
        'Series': ['0020,000E', '0020,0011'],   # Series Instance UID, Series Number
        'Image': ['0008,0018'],                 # SOP Instance UID
    }
    
    @classmethod
    def validate_dicom_tags(cls, dicom_data: Dict[str, Any], level: str = 'Patient') -> Tuple[bool, List[str]]:
        """
        Validate DICOM tags for specified level.
        
        Args:
            dicom_data: DICOM data as dictionary
            level: DICOM level (Patient, Study, Series, Image)
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if level not in cls.REQUIRED_TAGS:
            return False, [f"Unsupported DICOM level: {level}"]
        
        required_tags = cls.REQUIRED_TAGS[level]
        
        for tag in required_tags:
            if tag not in dicom_data:
                tag_name = cls._get_tag_name(tag)
                errors.append(f"Missing required DICOM tag: {tag} ({tag_name})")
        
        # Validate Patient ID format (should be NHS Number for UK)
        if level == 'Patient' and '0010,0020' in dicom_data:
            patient_id = dicom_data['0010,0020']
            if isinstance(patient_id, str):
                is_valid, error_msg = NHSNumberValidator.validate(patient_id)
                if not is_valid:
                    errors.append(f"Invalid Patient ID (NHS Number): {error_msg}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _get_tag_name(tag: str) -> str:
        """Get human-readable name for DICOM tag."""
        tag_names = {
            '0010,0010': 'Patient Name',
            '0010,0020': 'Patient ID',
            '0020,000D': 'Study Instance UID',
            '0020,0010': 'Study ID',
            '0020,000E': 'Series Instance UID',
            '0020,0011': 'Series Number',
            '0008,0018': 'SOP Instance UID',
        }
        return tag_names.get(tag, 'Unknown Tag')


class HealthcareDataValidator:
    """Main validator class for healthcare data."""
    
    def __init__(self):
        self.nhs_validator = NHSNumberValidator()
        self.hl7_validator = HL7Validator()
        self.fhir_validator = FHIRValidator()
        self.dicom_validator = DICOMValidator()
    
    def validate_healthcare_record(self, record: Dict[str, Any], data_type: str) -> Tuple[bool, List[str]]:
        """
        Validate healthcare record based on data type.
        
        Args:
            record: Healthcare record data
            data_type: Type of healthcare data (HL7, FHIR, DICOM, NHS)
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        if data_type.upper() == 'HL7':
            message = record.get('message', '')
            return self.hl7_validator.validate_message(message)
        
        elif data_type.upper() == 'FHIR':
            return self.fhir_validator.validate_resource(record)
        
        elif data_type.upper() == 'DICOM':
            level = record.get('level', 'Patient')
            return self.dicom_validator.validate_dicom_tags(record, level)
        
        elif data_type.upper() == 'NHS':
            return self._validate_nhs_record(record)
        
        else:
            return False, [f"Unsupported healthcare data type: {data_type}"]
    
    def _validate_nhs_record(self, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate NHS-specific record."""
        errors = []
        
        # Validate NHS Number if present
        nhs_number = record.get('nhs_number') or record.get('patient_id')
        if nhs_number:
            is_valid, error_msg = self.nhs_validator.validate(nhs_number)
            if not is_valid:
                errors.append(error_msg)
        
        # Validate date formats
        date_fields = ['date_of_birth', 'registration_date', 'last_updated']
        for field in date_fields:
            if field in record:
                if not self._validate_date_format(record[field]):
                    errors.append(f"Invalid date format for {field}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_date_format(date_value: Any) -> bool:
        """Validate date format (ISO 8601)."""
        if isinstance(date_value, (date, datetime)):
            return True
        
        if isinstance(date_value, str):
            try:
                datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                return True
            except ValueError:
                return False
        
        return False
