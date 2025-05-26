"""
Services for the transformation app.
"""

import logging
import re
import pandas as pd
from datetime import datetime
from .models import TransformationRule, TransformationJob, TransformationError

logger = logging.getLogger(__name__)


class TransformationService:
    """Service for transforming data based on mapping rules."""
    
    def __init__(self, transformation_job):
        """Initialize the transformation service with a job."""
        self.job = transformation_job
        self.entity_mapping = transformation_job.entity_mapping
        self.field_mappings = self.entity_mapping.field_mappings.all()
        self.transformation_rules = {}
        
        # Load transformation rules for each field mapping
        for field_mapping in self.field_mappings:
            self.transformation_rules[field_mapping.id] = field_mapping.transformation_rules.all().order_by('order')
    
    def transform_data(self, source_data):
        """Transform source data to target format."""
        transformed_data = []
        
        for record in source_data:
            try:
                transformed_record = self._transform_record(record)
                transformed_data.append(transformed_record)
                self.job.records_succeeded += 1
            except Exception as e:
                logger.error(f"Error transforming record: {str(e)}")
                self.job.records_failed += 1
                
                # Create error record
                TransformationError.objects.create(
                    job=self.job,
                    record_id=str(record.get('id', 'unknown')),
                    error_message=str(e),
                    error_details=record
                )
            
            self.job.records_processed += 1
        
        return transformed_data
    
    def _transform_record(self, record):
        """Transform a single record."""
        transformed_record = {}
        
        for field_mapping in self.field_mappings:
            source_field_name = field_mapping.source_field.name
            target_field_name = field_mapping.target_field.name
            
            # Get the source value
            source_value = record.get(source_field_name)
            
            # Apply transformation rules
            transformed_value = self._apply_transformation_rules(field_mapping.id, source_value)
            
            # Add to transformed record
            transformed_record[target_field_name] = transformed_value
        
        return transformed_record
    
    def _apply_transformation_rules(self, field_mapping_id, value):
        """Apply transformation rules to a value."""
        if value is None:
            return None
        
        rules = self.transformation_rules.get(field_mapping_id, [])
        
        for rule in rules:
            value = self._apply_rule(rule, value)
        
        return value
    
    def _apply_rule(self, rule, value):
        """Apply a single transformation rule."""
        rule_type = rule.rule_type
        rule_definition = rule.rule_definition
        
        if rule_type == 'STRING_REPLACE':
            pattern = rule_definition.get('pattern', '')
            replacement = rule_definition.get('replacement', '')
            return re.sub(pattern, replacement, str(value))
        
        elif rule_type == 'DATE_FORMAT':
            source_format = rule_definition.get('source_format', '')
            target_format = rule_definition.get('target_format', '')
            
            try:
                date_obj = datetime.strptime(str(value), source_format)
                return date_obj.strftime(target_format)
            except:
                return value
        
        elif rule_type == 'NUMBER_FORMAT':
            format_str = rule_definition.get('format', '')
            
            try:
                return format_str.format(float(value))
            except:
                return value
        
        elif rule_type == 'CONCATENATE':
            fields = rule_definition.get('fields', [])
            separator = rule_definition.get('separator', '')
            
            # In a real implementation, this would need to access other field values
            # For now, we'll just return the original value
            return value
        
        elif rule_type == 'SPLIT':
            separator = rule_definition.get('separator', '')
            index = rule_definition.get('index', 0)
            
            try:
                parts = str(value).split(separator)
                return parts[index] if 0 <= index < len(parts) else value
            except:
                return value
        
        elif rule_type == 'CUSTOM_FUNCTION':
            function_name = rule_definition.get('function', '')
            
            # In a real implementation, this would dynamically call a registered function
            # For now, we'll just return the original value
            return value
        
        return value
