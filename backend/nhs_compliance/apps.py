"""
NHS Compliance App Configuration
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class NhsComplianceConfig(AppConfig):
    """NHS Compliance app configuration."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'nhs_compliance'
    verbose_name = _('NHS Compliance')

    def ready(self):
        """Initialize NHS compliance features when app is ready."""
        # Register NHS compliance checks
        self._register_compliance_checks()

        # Initialize DSPT monitoring
        self._initialize_dspt_monitoring()

    def _register_compliance_checks(self):
        """Register NHS compliance validation checks."""
        try:
            from django.core.checks import register
            from . import checks

            # Register NHS-specific system checks
            register(checks.check_nhs_encryption_config, 'nhs_compliance')
            register(checks.check_dspt_requirements, 'nhs_compliance')
            register(checks.check_audit_retention, 'nhs_compliance')

        except ImportError:
            pass  # Checks module not yet created

    def _initialize_dspt_monitoring(self):
        """Initialize DSPT compliance monitoring."""
        try:
            from django.conf import settings

            # Enable DSPT monitoring if configured
            if getattr(settings, 'NHS_DSPT_MONITORING_ENABLED', True):
                from .monitoring import DSPTMonitor
                DSPTMonitor.initialize()

        except ImportError:
            pass  # Monitoring module not yet created
