"""
Services for the validation app.
"""

import logging
import re
from datetime import datetime
from .models import ValidationRule, ValidationJob, ValidationError

logger = logging.getLogger(__name__)


class ValidationService:
    """Service for validating data based on validation rules."""
    
    def __init__(self, validation_job):
        """Initialize the validation service with a job."""
        self.job = validation_job
        self.entity_mapping = validation_job.entity_mapping
        self.rules = ValidationRule.objects.filter(entity_mapping=self.entity_mapping)
    
    def validate_data(self, data):
        """Validate a dataset against the rules."""
        for record in data:
            record_id = str(record.get('id', 'unknown'))
            record_passed = True
            
            for rule in self.rules:
                if not self._validate_record_against_rule(record, record_id, rule):
                    record_passed = False
            
            if record_passed:
                self.job.records_passed += 1
            else:
                self.job.records_failed += 1
            
            self.job.records_processed += 1
        
        return self.job.records_failed == 0
    
    def _validate_record_against_rule(self, record, record_id, rule):
        """Validate a single record against a rule."""
        field_name = rule.field_name
        field_value = record.get(field_name)
        rule_type = rule.rule_type
        rule_definition = rule.rule_definition
        
        try:
            if rule_type == 'REQUIRED':
                if field_value is None or field_value == '':
                    self._create_error(rule, record_id, field_name, "Field is required but missing or empty")
                    return False
            
            elif rule_type == 'FORMAT':
                pattern = rule_definition.get('pattern', '')
                if field_value is not None and not re.match(pattern, str(field_value)):
                    self._create_error(rule, record_id, field_name, f"Field does not match required format: {pattern}")
                    return False
            
            elif rule_type == 'RANGE':
                min_value = rule_definition.get('min')
                max_value = rule_definition.get('max')
                
                if field_value is not None:
                    if min_value is not None and float(field_value) < float(min_value):
                        self._create_error(rule, record_id, field_name, f"Value {field_value} is less than minimum {min_value}")
                        return False
                    
                    if max_value is not None and float(field_value) > float(max_value):
                        self._create_error(rule, record_id, field_name, f"Value {field_value} is greater than maximum {max_value}")
                        return False
            
            elif rule_type == 'UNIQUE':
                # In a real implementation, this would check for uniqueness across the dataset
                # For now, we'll just assume it passes
                pass
            
            elif rule_type == 'REFERENTIAL':
                # In a real implementation, this would check for referential integrity
                # For now, we'll just assume it passes
                pass
            
            elif rule_type == 'CUSTOM':
                # In a real implementation, this would execute a custom validation function
                # For now, we'll just assume it passes
                pass
            
            return True
        
        except Exception as e:
            logger.error(f"Error validating rule {rule.name} for record {record_id}: {str(e)}")
            self._create_error(rule, record_id, field_name, f"Validation error: {str(e)}")
            return False
    
    def _create_error(self, rule, record_id, field_name, message):
        """Create a validation error record."""
        severity = 'CRITICAL' if rule.is_critical else 'ERROR'
        
        ValidationError.objects.create(
            job=self.job,
            rule=rule,
            record_id=record_id,
            field_name=field_name,
            error_message=message,
            severity=severity
        )
