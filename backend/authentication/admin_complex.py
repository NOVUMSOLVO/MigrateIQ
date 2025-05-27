from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User
# from .models import UserInvitation, UserSession  # Temporarily disabled


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for User model."""

    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'tenant', 'role', 'is_active', 'is_verified',
        'created_at', 'last_login'
    )
    list_filter = (
        'is_active', 'is_verified', 'role', 'tenant',
        'created_at', 'last_login'
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_login')

    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        (_('Personal info'), {
            'fields': (
                'first_name', 'last_name', 'email', 'phone_number',
                'language', 'timezone'
            )
        }),
        (_('Tenant & Role'), {
            'fields': ('tenant', 'role')
        }),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_verified', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            )
        }),
        (_('Security'), {
            'fields': (
                'two_factor_enabled', 'failed_login_attempts',
                'account_locked_until', 'last_login_ip'
            )
        }),
        (_('Preferences'), {
            'fields': ('preferences',),
            'classes': ('collapse',)
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'first_name', 'last_name',
                'tenant', 'role', 'password1', 'password2'
            ),
        }),
    )

    def get_queryset(self, request):
        """Filter users by tenant for non-superusers."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request, 'tenant') and request.tenant:
            return qs.filter(tenant=request.tenant)
        return qs.none()


# Temporarily disabled until UserInvitation model is available
# @admin.register(UserInvitation)
# class UserInvitationAdmin(admin.ModelAdmin):
    """Admin configuration for UserInvitation model."""

    list_display = (
        'email', 'role', 'tenant', 'invited_by',
        'status', 'created_at', 'expires_at'
    )
    list_filter = ('status', 'role', 'tenant', 'created_at')
    search_fields = ('email', 'invited_by__username', 'tenant__name')
    readonly_fields = ('id', 'created_at', 'accepted_at')
    ordering = ('-created_at',)

    fieldsets = (
        (None, {
            'fields': ('email', 'role', 'tenant', 'invited_by')
        }),
        (_('Status'), {
            'fields': ('status', 'expires_at', 'accepted_at')
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Filter invitations by tenant for non-superusers."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request, 'tenant') and request.tenant:
            return qs.filter(tenant=request.tenant)
        return qs.none()

    def save_model(self, request, obj, form, change):
        """Set invited_by to current user if not set."""
        if not change and not obj.invited_by:
            obj.invited_by = request.user
        super().save_model(request, obj, form, change)


# Temporarily disabled until UserSession model is available
# @admin.register(UserSession)
# class UserSessionAdmin(admin.ModelAdmin):
    """Admin configuration for UserSession model."""

    list_display = (
        'user', 'ip_address', 'is_active',
        'created_at', 'last_activity'
    )
    list_filter = ('is_active', 'created_at', 'last_activity')
    search_fields = ('user__username', 'user__email', 'ip_address')
    readonly_fields = ('id', 'created_at', 'last_activity')
    ordering = ('-created_at',)

    fieldsets = (
        (None, {
            'fields': ('user', 'session_key', 'ip_address', 'user_agent')
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'last_activity'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Filter sessions by tenant for non-superusers."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request, 'tenant') and request.tenant:
            return qs.filter(user__tenant=request.tenant)
        return qs.none()

    def has_add_permission(self, request):
        """Disable manual session creation."""
        return False