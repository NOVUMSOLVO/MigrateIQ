"""
Django app configuration for the validation app.
"""

from django.apps import AppConfig


class ValidationConfig(AppConfig):
    """Configuration for the validation app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'validation'
