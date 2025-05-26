"""
Serializers for the analyzer app.
"""
from rest_framework import serializers
from .models import DataSource, Entity, Field

class FieldSerializer(serializers.ModelSerializer):
    """Serializer for the Field model."""
    
    class Meta:
        model = Field
        fields = [
            'id', 'name', 'description', 'original_name', 'data_type',
            'is_primary_key', 'is_nullable', 'sample_values', 'created_at', 'updated_at'
        ]

class EntitySerializer(serializers.ModelSerializer):
    """Serializer for the Entity model."""
    
    fields = FieldSerializer(many=True, read_only=True)
    
    class Meta:
        model = Entity
        fields = [
            'id', 'name', 'description', 'original_name', 'record_count',
            'created_at', 'updated_at', 'fields'
        ]

class DataSourceSerializer(serializers.ModelSerializer):
    """Serializer for the DataSource model."""
    
    entities = EntitySerializer(many=True, read_only=True)
    
    class Meta:
        model = DataSource
        fields = [
            'id', 'name', 'source_type', 'connection_string',
            'created_at', 'updated_at', 'entities'
        ]
        extra_kwargs = {
            'connection_string': {'write_only': True}
        }

class DataSourceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a DataSource."""
    
    class Meta:
        model = DataSource
        fields = ['name', 'source_type', 'connection_string']
