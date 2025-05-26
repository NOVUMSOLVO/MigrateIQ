"""
Serializers for the transformation app.
"""

from rest_framework import serializers
from .models import TransformationRule, TransformationJob, TransformationError


class TransformationRuleSerializer(serializers.ModelSerializer):
    """Serializer for TransformationRule model."""
    
    class Meta:
        model = TransformationRule
        fields = '__all__'


class TransformationJobSerializer(serializers.ModelSerializer):
    """Serializer for TransformationJob model."""
    
    source_entity_name = serializers.ReadOnlyField(source='entity_mapping.source_entity.name')
    target_entity_name = serializers.ReadOnlyField(source='entity_mapping.target_entity.name')
    
    class Meta:
        model = TransformationJob
        fields = '__all__'


class TransformationErrorSerializer(serializers.ModelSerializer):
    """Serializer for TransformationError model."""
    
    class Meta:
        model = TransformationError
        fields = '__all__'
