from django.db import models

# Create your models here.
class DataSource(models.Model):
    """Model representing a data source to be analyzed"""
    name = models.CharField(max_length=100)
    source_type = models.CharField(max_length=50)
    connection_string = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Entity(models.Model):
    """Model representing an entity (table/collection) in a data source"""
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='entities')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    original_name = models.CharField(max_length=100)
    record_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.data_source.name} - {self.name}"

    class Meta:
        verbose_name_plural = "entities"


class Field(models.Model):
    """Model representing a field (column/attribute) in an entity"""
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='fields')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    original_name = models.CharField(max_length=100)
    data_type = models.CharField(max_length=50)
    is_primary_key = models.BooleanField(default=False)
    is_nullable = models.BooleanField(default=True)
    sample_values = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.entity.name} - {self.name}"
