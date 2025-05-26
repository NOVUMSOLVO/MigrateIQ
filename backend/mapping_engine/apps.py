"""
Django app configuration for the mapping_engine app.
"""

from django.apps import AppConfig


class MappingEngineConfig(AppConfig):
    """Configuration for the mapping_engine app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mapping_engine'
