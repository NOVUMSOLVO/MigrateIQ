"""
Serializers for the validation app.
"""

from rest_framework import serializers
from .models import ValidationRule, ValidationJob, ValidationError


class ValidationRuleSerializer(serializers.ModelSerializer):
    """Serializer for ValidationRule model."""
    
    class Meta:
        model = ValidationRule
        fields = '__all__'


class ValidationJobSerializer(serializers.ModelSerializer):
    """Serializer for ValidationJob model."""
    
    source_entity_name = serializers.ReadOnlyField(source='entity_mapping.source_entity.name')
    target_entity_name = serializers.ReadOnlyField(source='entity_mapping.target_entity.name')
    
    class Meta:
        model = ValidationJob
        fields = '__all__'


class ValidationErrorSerializer(serializers.ModelSerializer):
    """Serializer for ValidationError model."""
    
    rule_name = serializers.ReadOnlyField(source='rule.name')
    
    class Meta:
        model = ValidationError
        fields = '__all__'
