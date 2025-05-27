"""
Healthcare Standards App Configuration
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class HealthcareStandardsConfig(AppConfig):
    """Healthcare Standards app configuration."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'healthcare_standards'
    verbose_name = _('Healthcare Standards')

    def ready(self):
        """Initialize healthcare standards when app is ready."""
        # Register healthcare validators
        self._register_validators()

        # Initialize standards support
        self._initialize_standards()

    def _register_validators(self):
        """Register healthcare data validators."""
        try:
            from .validators import HealthcareDataValidator

            # Initialize global validator instance
            global healthcare_validator
            healthcare_validator = HealthcareDataValidator()

        except ImportError:
            pass

    def _initialize_standards(self):
        """Initialize healthcare standards support."""
        try:
            from django.conf import settings

            # Enable healthcare standards if configured
            if getattr(settings, 'HEALTHCARE_STANDARDS_ENABLED', True):
                try:
                    from . import SUPPORTED_STANDARDS, NHS_STANDARDS

                    # Log supported standards
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"Healthcare standards initialized: {list(SUPPORTED_STANDARDS.keys())}")
                    logger.info(f"NHS standards initialized: {list(NHS_STANDARDS.keys())}")
                except ImportError:
                    pass

        except ImportError:
            pass
