"""
Models for the validation app.
"""

from django.db import models
from orchestrator.models import MigrationProject
from mapping_engine.models import Mapping


class ValidationRule(models.Model):
    """Model representing a validation rule."""
    
    TYPE_CHOICES = [
        ('REQUIRED', 'Required Field'),
        ('FORMAT', 'Format Check'),
        ('RANGE', 'Range Check'),
        ('UNIQUE', 'Uniqueness Check'),
        ('REFERENTIAL', 'Referential Integrity'),
        ('CUSTOM', 'Custom Validation'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    rule_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    entity_mapping = models.ForeignKey(Mapping, on_delete=models.CASCADE, related_name='validation_rules')
    field_name = models.CharField(max_length=255)
    rule_definition = models.JSONField()
    is_critical = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name


class ValidationJob(models.Model):
    """Model representing a validation job."""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    project = models.ForeignKey(MigrationProject, on_delete=models.CASCADE, related_name='validation_jobs')
    entity_mapping = models.ForeignKey(Mapping, on_delete=models.CASCADE, related_name='validation_jobs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    records_processed = models.IntegerField(default=0)
    records_passed = models.IntegerField(default=0)
    records_failed = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.project.name} - {self.entity_mapping.source_entity.name} Validation"


class ValidationError(models.Model):
    """Model representing a validation error."""
    
    SEVERITY_CHOICES = [
        ('INFO', 'Information'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    job = models.ForeignKey(ValidationJob, on_delete=models.CASCADE, related_name='errors')
    rule = models.ForeignKey(ValidationRule, on_delete=models.CASCADE, related_name='errors')
    record_id = models.CharField(max_length=255)
    field_name = models.CharField(max_length=255)
    error_message = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='ERROR')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.job} - {self.rule.name} - Record {self.record_id}"
