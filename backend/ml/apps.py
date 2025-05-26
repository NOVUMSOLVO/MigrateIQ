"""
Django app configuration for the ml app.
"""

from django.apps import AppConfig


class MlConfig(AppConfig):
    """Configuration for the ml app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ml'
