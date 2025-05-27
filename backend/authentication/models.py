from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid


class User(AbstractUser):
    """Custom user model with additional fields."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Profile information
    first_name = models.CharField(_('First name'), max_length=150)
    last_name = models.CharField(_('Last name'), max_length=150)
    email = models.EmailField(_('Email address'), unique=True)
    phone = models.CharField(_('Phone number'), max_length=20, blank=True)

    # Role and permissions
    role = models.CharField(
        _('Role'),
        max_length=20,
        choices=[
            ('admin', _('Admin')),
            ('manager', _('Manager')),
            ('analyst', _('Analyst')),
            ('viewer', _('Viewer')),
        ],
        default='viewer'
    )

    # Preferences
    language = models.CharField(
        _('Language'),
        max_length=10,
        choices=[
            ('en', _('English')),
            ('es', _('Spanish')),
            ('fr', _('French')),
            ('de', _('German')),
            ('it', _('Italian')),
            ('pt', _('Portuguese')),
            ('zh', _('Chinese')),
            ('ar', _('Arabic')),
        ],
        default='en'
    )
    timezone = models.CharField(
        _('Timezone'),
        max_length=50,
        default='UTC'
    )
    preferences = models.JSONField(_('Preferences'), default=dict, blank=True)

    # Security
    is_verified = models.BooleanField(_('Is verified'), default=False)
    two_factor_enabled = models.BooleanField(_('Two-factor enabled'), default=False)
    last_password_change = models.DateTimeField(_('Last password change'), null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)

    # Override username requirement
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['email']

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_full_name(self):
        """Return the full name of the user."""
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        """Return the short name of the user."""
        return self.first_name

    def has_role(self, role):
        """Check if user has a specific role."""
        return self.role == role

    def is_admin(self):
        """Check if user is an admin."""
        return self.role == 'admin' or self.is_superuser

    def is_manager(self):
        """Check if user is a manager."""
        return self.role in ['admin', 'manager'] or self.is_superuser

    def can_manage_users(self):
        """Check if user can manage other users."""
        return self.role in ['admin', 'manager']

    def can_create_projects(self):
        """Check if user can create projects."""
        return self.role in ['admin', 'manager', 'analyst']

    def can_view_analytics(self):
        """Check if user can view analytics."""
        return self.role in ['admin', 'manager']
