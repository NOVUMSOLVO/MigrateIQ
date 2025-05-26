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

    # Tenant relationship
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='users',
        verbose_name=_('Tenant'),
        null=True,
        blank=True
    )

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

    # Profile settings
    language = models.CharField(
        _('Language'),
        max_length=10,
        choices=[
            ('en', _('English')),
            ('es', _('Spanish')),
            ('fr', _('French')),
            ('de', _('German')),
            ('zh', _('Chinese')),
            ('ja', _('Japanese')),
            ('ar', _('Arabic')),
            ('he', _('Hebrew')),
        ],
        default='en'
    )

    timezone = models.CharField(
        _('Timezone'),
        max_length=50,
        default='UTC'
    )

    # Preferences
    preferences = models.JSONField(_('Preferences'), default=dict, blank=True)

    # Security
    is_verified = models.BooleanField(_('Is verified'), default=False)
    last_login_ip = models.GenericIPAddressField(_('Last login IP'), null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(_('Failed login attempts'), default=0)
    locked_until = models.DateTimeField(_('Locked until'), null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['email']
        indexes = [
            models.Index(fields=['tenant', 'email']),
            models.Index(fields=['tenant', 'role']),
        ]

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
        """Check if user is a manager or higher."""
        return self.role in ['admin', 'manager'] or self.is_superuser

    def can_manage_users(self):
        """Check if user can manage other users."""
        return self.is_admin()

    def can_create_projects(self):
        """Check if user can create projects."""
        return self.role in ['admin', 'manager', 'analyst']

    def can_view_analytics(self):
        """Check if user can view analytics."""
        return self.role in ['admin', 'manager']


class UserGroup(models.Model):
    """Model for user groups within a tenant."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='user_groups',
        verbose_name=_('Tenant')
    )
    name = models.CharField(_('Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True)

    # Permissions
    permissions = models.JSONField(_('Permissions'), default=dict, blank=True)

    # Members
    members = models.ManyToManyField(
        User,
        through='UserGroupMembership',
        related_name='groups',
        verbose_name=_('Members')
    )

    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)

    class Meta:
        verbose_name = _('User Group')
        verbose_name_plural = _('User Groups')
        unique_together = [['tenant', 'name']]
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"


class UserGroupMembership(models.Model):
    """Model for user group membership with roles."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='group_memberships'
    )
    group = models.ForeignKey(
        UserGroup,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    role = models.CharField(
        _('Role in Group'),
        max_length=20,
        choices=[
            ('member', _('Member')),
            ('moderator', _('Moderator')),
            ('admin', _('Admin')),
        ],
        default='member'
    )
    joined_at = models.DateTimeField(_('Joined at'), auto_now_add=True)

    class Meta:
        verbose_name = _('User Group Membership')
        verbose_name_plural = _('User Group Memberships')
        unique_together = [['user', 'group']]


class UserInvitation(models.Model):
    """Model for user invitations."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='invitations',
        verbose_name=_('Tenant')
    )
    invited_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_invitations',
        verbose_name=_('Invited by')
    )

    email = models.EmailField(_('Email address'))
    role = models.CharField(
        _('Role'),
        max_length=20,
        choices=User._meta.get_field('role').choices
    )

    # Optional group assignment
    groups = models.ManyToManyField(
        UserGroup,
        blank=True,
        related_name='invitations',
        verbose_name=_('Groups')
    )

    # Status
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=[
            ('pending', _('Pending')),
            ('accepted', _('Accepted')),
            ('expired', _('Expired')),
            ('cancelled', _('Cancelled')),
        ],
        default='pending'
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    expires_at = models.DateTimeField(_('Expires at'))
    accepted_at = models.DateTimeField(_('Accepted at'), null=True, blank=True)

    class Meta:
        verbose_name = _('User invitation')
        verbose_name_plural = _('User invitations')
        unique_together = [['tenant', 'email', 'status']]
        ordering = ['-created_at']

    def __str__(self):
        return f"Invitation for {self.email} to {self.tenant.name}"


class UserActivity(models.Model):
    """Model for tracking user activities."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name=_('User')
    )
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='user_activities',
        verbose_name=_('Tenant'),
        null=True,
        blank=True
    )

    # Activity details
    activity_type = models.CharField(
        _('Activity Type'),
        max_length=50,
        choices=[
            ('login', _('Login')),
            ('logout', _('Logout')),
            ('password_change', _('Password Change')),
            ('profile_update', _('Profile Update')),
            ('project_create', _('Project Create')),
            ('project_update', _('Project Update')),
            ('project_delete', _('Project Delete')),
            ('data_export', _('Data Export')),
            ('settings_change', _('Settings Change')),
            ('api_access', _('API Access')),
        ]
    )
    description = models.TextField(_('Description'), blank=True)

    # Context
    ip_address = models.GenericIPAddressField(_('IP Address'), null=True, blank=True)
    user_agent = models.TextField(_('User Agent'), blank=True)
    session_key = models.CharField(_('Session Key'), max_length=40, blank=True)

    # Additional data
    metadata = models.JSONField(_('Metadata'), default=dict, blank=True)

    timestamp = models.DateTimeField(_('Timestamp'), auto_now_add=True)

    class Meta:
        verbose_name = _('User Activity')
        verbose_name_plural = _('User Activities')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['tenant', 'timestamp']),
            models.Index(fields=['activity_type', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.activity_type} at {self.timestamp}"


class UserSession(models.Model):
    """Model for tracking user sessions."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name=_('User')
    )
    session_key = models.CharField(_('Session Key'), max_length=40, unique=True)

    # Session details
    ip_address = models.GenericIPAddressField(_('IP Address'), null=True, blank=True)
    user_agent = models.TextField(_('User Agent'), blank=True)
    device_info = models.JSONField(_('Device Info'), default=dict, blank=True)

    # Location (optional)
    country = models.CharField(_('Country'), max_length=2, blank=True)
    city = models.CharField(_('City'), max_length=100, blank=True)

    # Session status
    is_active = models.BooleanField(_('Is Active'), default=True)
    last_activity = models.DateTimeField(_('Last Activity'), auto_now=True)

    # Timestamps
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    expires_at = models.DateTimeField(_('Expires at'), null=True, blank=True)

    class Meta:
        verbose_name = _('User Session')
        verbose_name_plural = _('User Sessions')
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_key']),
            models.Index(fields=['last_activity']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.ip_address} ({self.created_at})"

    def is_expired(self):
        """Check if session is expired."""
        if not self.expires_at:
            return False
        from django.utils import timezone
        return timezone.now() > self.expires_at

