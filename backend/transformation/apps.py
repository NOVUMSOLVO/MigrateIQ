"""
Django app configuration for the transformation app.
"""

from django.apps import AppConfig


class TransformationConfig(AppConfig):
    """Configuration for the transformation app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'transformation'
