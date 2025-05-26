"""
Models for the ml app.
"""

from django.db import models


class MLModel(models.Model):
    """Model representing a machine learning model."""
    
    TYPE_CHOICES = [
        ('SCHEMA_RECOGNITION', 'Schema Recognition Model'),
        ('FIELD_MAPPING', 'Field Mapping Model'),
        ('DATA_QUALITY', 'Data Quality Enhancement Model'),
    ]
    
    name = models.CharField(max_length=255)
    model_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.TextField(blank=True)
    version = models.CharField(max_length=50)
    file_path = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.name} v{self.version}"


class TrainingJob(models.Model):
    """Model representing a model training job."""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    model = models.ForeignKey(MLModel, on_delete=models.CASCADE, related_name='training_jobs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    training_parameters = models.JSONField(default=dict)
    metrics = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.model.name} Training - {self.started_at}"


class ModelPrediction(models.Model):
    """Model representing a prediction made by a model."""
    
    model = models.ForeignKey(MLModel, on_delete=models.CASCADE, related_name='predictions')
    input_data = models.JSONField()
    output_data = models.JSONField()
    confidence_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.model.name} Prediction - {self.created_at}"
