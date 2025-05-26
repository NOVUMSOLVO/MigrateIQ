from django.db import models

class MigrationProject(models.Model):
    """Model representing a migration project"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    source_system = models.CharField(max_length=100)
    target_system = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20,
        choices=[
            ('DRAFT', 'Draft'),
            ('PLANNING', 'Planning'),
            ('IN_PROGRESS', 'In Progress'),
            ('COMPLETED', 'Completed'),
            ('FAILED', 'Failed'),
        ],
        default='DRAFT'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class MigrationTask(models.Model):
    """Model representing a task within a migration project"""
    project = models.ForeignKey(MigrationProject, on_delete=models.CASCADE, related_name='tasks')
    name = models.CharField(max_length=100)
    task_type = models.CharField(
        max_length=20,
        choices=[
            ('ANALYSIS', 'Data Analysis'),
            ('MAPPING', 'Data Mapping'),
            ('TRANSFORMATION', 'Data Transformation'),
            ('VALIDATION', 'Data Validation'),
            ('MIGRATION', 'Data Migration'),
        ]
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('IN_PROGRESS', 'In Progress'),
            ('COMPLETED', 'Completed'),
            ('FAILED', 'Failed'),
        ],
        default='PENDING'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.name} - {self.name}"
