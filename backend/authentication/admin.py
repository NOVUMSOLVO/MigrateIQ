from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for custom User model."""

    list_display = (
        'email', 'first_name', 'last_name', 'role',
        'is_active', 'is_verified', 'created_at'
    )
    list_filter = ('role', 'is_active', 'is_verified', 'created_at')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    readonly_fields = ('id', 'created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'phone')
        }),
        (_('Permissions'), {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        (_('Preferences'), {
            'fields': ('language', 'timezone', 'preferences'),
            'classes': ('collapse',)
        }),
        (_('Security'), {
            'fields': ('is_verified', 'two_factor_enabled', 'last_password_change'),
            'classes': ('collapse',)
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'role'),
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

    def save_model(self, request, obj, form, change):
        """Set tenant for new users if not superuser."""
        if not change and not request.user.is_superuser:
            if hasattr(request, 'tenant') and request.tenant:
                obj.tenant = request.tenant
        super().save_model(request, obj, form, change)
