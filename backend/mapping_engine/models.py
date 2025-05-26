"""
Models for the mapping_engine app.
"""

from django.db import models
from analyzer.models import Entity, Field


class Mapping(models.Model):
    """Model representing a mapping between source and target entities."""
    
    source_entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='source_mappings')
    target_entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='target_mappings')
    confidence_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.source_entity.name} -> {self.target_entity.name}"


class FieldMapping(models.Model):
    """Model representing a mapping between source and target fields."""
    
    mapping = models.ForeignKey(Mapping, on_delete=models.CASCADE, related_name='field_mappings')
    source_field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='source_field_mappings')
    target_field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='target_field_mappings')
    confidence_score = models.FloatField(default=0.0)
    transformation_rule = models.TextField(blank=True)
    is_manually_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.source_field.name} -> {self.target_field.name}"


class MappingRule(models.Model):
    """Model representing a predefined mapping rule."""
    
    RULE_TYPE_CHOICES = [
        ('EXACT_MATCH', 'Exact Match'),
        ('SYNONYM', 'Synonym'),
        ('PATTERN', 'Pattern'),
        ('CUSTOM', 'Custom'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPE_CHOICES)
    source_pattern = models.CharField(max_length=255)
    target_pattern = models.CharField(max_length=255)
    priority = models.IntegerField(default=0)
    
    def __str__(self):
        return self.name
