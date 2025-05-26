"""
Serializers for the orchestrator app.
"""
from rest_framework import serializers
from .models import MigrationProject, MigrationTask

class MigrationTaskSerializer(serializers.ModelSerializer):
    """Serializer for the MigrationTask model."""
    
    class Meta:
        model = MigrationTask
        fields = [
            'id', 'name', 'task_type', 'status',
            'created_at', 'updated_at'
        ]

class MigrationProjectSerializer(serializers.ModelSerializer):
    """Serializer for the MigrationProject model."""
    
    tasks = MigrationTaskSerializer(many=True, read_only=True)
    
    class Meta:
        model = MigrationProject
        fields = [
            'id', 'name', 'description', 'source_system', 'target_system',
            'status', 'created_at', 'updated_at', 'tasks'
        ]

class MigrationProjectCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a MigrationProject."""
    
    class Meta:
        model = MigrationProject
        fields = ['name', 'description', 'source_system', 'target_system']
