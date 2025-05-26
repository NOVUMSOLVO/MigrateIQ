"""
Serializers for the mapping_engine app.
"""

from rest_framework import serializers
from .models import Mapping, FieldMapping, MappingRule


class FieldMappingSerializer(serializers.ModelSerializer):
    """Serializer for FieldMapping model."""
    
    source_field_name = serializers.ReadOnlyField(source='source_field.name')
    target_field_name = serializers.ReadOnlyField(source='target_field.name')
    
    class Meta:
        model = FieldMapping
        fields = '__all__'


class MappingSerializer(serializers.ModelSerializer):
    """Serializer for Mapping model."""
    
    source_entity_name = serializers.ReadOnlyField(source='source_entity.name')
    target_entity_name = serializers.ReadOnlyField(source='target_entity.name')
    field_mappings = FieldMappingSerializer(many=True, read_only=True)
    
    class Meta:
        model = Mapping
        fields = '__all__'


class MappingRuleSerializer(serializers.ModelSerializer):
    """Serializer for MappingRule model."""
    
    class Meta:
        model = MappingRule
        fields = '__all__'
