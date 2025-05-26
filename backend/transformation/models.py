"""
Models for the transformation app.
"""

from django.db import models
from orchestrator.models import MigrationProject
from mapping_engine.models import Mapping, FieldMapping


class TransformationRule(models.Model):
    """Model representing a transformation rule."""
    
    TYPE_CHOICES = [
        ('STRING_REPLACE', 'String Replace'),
        ('DATE_FORMAT', 'Date Format'),
        ('NUMBER_FORMAT', 'Number Format'),
        ('CONCATENATE', 'Concatenate'),
        ('SPLIT', 'Split'),
        ('CUSTOM_FUNCTION', 'Custom Function'),
    ]
    
    field_mapping = models.ForeignKey(FieldMapping, on_delete=models.CASCADE, related_name='transformation_rules')
    rule_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    rule_definition = models.JSONField()
    order = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.field_mapping} - {self.get_rule_type_display()}"
    
    class Meta:
        ordering = ['order']


class TransformationJob(models.Model):
    """Model representing a transformation job."""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    project = models.ForeignKey(MigrationProject, on_delete=models.CASCADE, related_name='transformation_jobs')
    entity_mapping = models.ForeignKey(Mapping, on_delete=models.CASCADE, related_name='transformation_jobs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    records_processed = models.IntegerField(default=0)
    records_succeeded = models.IntegerField(default=0)
    records_failed = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.project.name} - {self.entity_mapping.source_entity.name} Transformation"


class TransformationError(models.Model):
    """Model representing an error during transformation."""
    
    job = models.ForeignKey(TransformationJob, on_delete=models.CASCADE, related_name='errors')
    record_id = models.CharField(max_length=255)
    error_message = models.TextField()
    error_details = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.job} - Record {self.record_id}"
