from rest_framework import permissions
from django.utils.translation import gettext_lazy as _


class IsSuperUser(permissions.BasePermission):
    """Permission class that only allows superusers."""
    
    message = _('You must be a superuser to perform this action.')
    
    def has_permission(self, request, view):
        """Check if user is a superuser."""
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_superuser
        )


class IsTenantAdmin(permissions.BasePermission):
    """Permission class that allows tenant admins."""
    
    message = _('You must be a tenant admin to perform this action.')
    
    def has_permission(self, request, view):
        """Check if user is a tenant admin."""
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Check if user has admin role
        return request.user.role in ['admin', 'owner']
    
    def has_object_permission(self, request, view, obj):
        """Check if user can access this specific object."""
        if not self.has_permission(request, view):
            return False
        
        # Check if object belongs to user's tenant
        if hasattr(obj, 'tenant'):
            return obj.tenant == getattr(request, 'tenant', None)
        
        return True


class IsSuperUserOrTenantAdmin(permissions.BasePermission):
    """Permission class that allows superusers or tenant admins."""
    
    message = _('You must be a superuser or tenant admin to perform this action.')
    
    def has_permission(self, request, view):
        """Check if user is superuser or tenant admin."""
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Allow superusers
        if request.user.is_superuser:
            return True
        
        # Allow tenant admins
        return request.user.role in ['admin', 'owner']
    
    def has_object_permission(self, request, view, obj):
        """Check if user can access this specific object."""
        if not self.has_permission(request, view):
            return False
        
        # Superusers can access everything
        if request.user.is_superuser:
            return True
        
        # Tenant admins can only access objects in their tenant
        if hasattr(obj, 'tenant'):
            return obj.tenant == getattr(request, 'tenant', None)
        
        return True


class IsTenantMember(permissions.BasePermission):
    """Permission class that allows any tenant member."""
    
    message = _('You must be a member of this tenant to perform this action.')
    
    def has_permission(self, request, view):
        """Check if user is a tenant member."""
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Check if user belongs to a tenant
        return hasattr(request, 'tenant') and request.tenant is not None
    
    def has_object_permission(self, request, view, obj):
        """Check if user can access this specific object."""
        if not self.has_permission(request, view):
            return False
        
        # Check if object belongs to user's tenant
        if hasattr(obj, 'tenant'):
            return obj.tenant == getattr(request, 'tenant', None)
        
        # Check if object belongs to user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return True


class IsOwnerOrTenantAdmin(permissions.BasePermission):
    """Permission class that allows object owners or tenant admins."""
    
    message = _('You must be the owner or a tenant admin to perform this action.')
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return bool(request.user and request.user.is_authenticated)
    
    def has_object_permission(self, request, view, obj):
        """Check if user is owner or tenant admin."""
        if not self.has_permission(request, view):
            return False
        
        # Superusers can access everything
        if request.user.is_superuser:
            return True
        
        # Check if user is tenant admin
        if request.user.role in ['admin', 'owner']:
            # Ensure object belongs to same tenant
            if hasattr(obj, 'tenant'):
                return obj.tenant == getattr(request, 'tenant', None)
            return True
        
        # Check if user is the owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False


class CanManageUsers(permissions.BasePermission):
    """Permission class for user management operations."""
    
    message = _('You do not have permission to manage users.')
    
    def has_permission(self, request, view):
        """Check if user can manage users."""
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Superusers can manage all users
        if request.user.is_superuser:
            return True
        
        # Check if user has user management permission
        if hasattr(request.user, 'can_manage_users'):
            return request.user.can_manage_users()
        
        # Default to admin/owner roles
        return request.user.role in ['admin', 'owner']


class CanManageProjects(permissions.BasePermission):
    """Permission class for project management operations."""
    
    message = _('You do not have permission to manage projects.')
    
    def has_permission(self, request, view):
        """Check if user can manage projects."""
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Superusers can manage all projects
        if request.user.is_superuser:
            return True
        
        # Check if user has project management permission
        if hasattr(request.user, 'can_manage_projects'):
            return request.user.can_manage_projects()
        
        # Default to admin/owner/manager roles
        return request.user.role in ['admin', 'owner', 'manager']


class CanViewAuditLogs(permissions.BasePermission):
    """Permission class for viewing audit logs."""
    
    message = _('You do not have permission to view audit logs.')
    
    def has_permission(self, request, view):
        """Check if user can view audit logs."""
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Superusers can view all audit logs
        if request.user.is_superuser:
            return True
        
        # Only admins and owners can view audit logs
        return request.user.role in ['admin', 'owner']


class ReadOnlyOrTenantAdmin(permissions.BasePermission):
    """Permission class that allows read-only access or tenant admin write access."""
    
    message = _('You do not have permission to modify this resource.')
    
    def has_permission(self, request, view):
        """Check permissions based on request method."""
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Allow read operations for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Allow write operations for superusers and tenant admins
        if request.user.is_superuser:
            return True
        
        return request.user.role in ['admin', 'owner']
    
    def has_object_permission(self, request, view, obj):
        """Check object-level permissions."""
        if not self.has_permission(request, view):
            return False
        
        # Read permissions for all authenticated users in same tenant
        if request.method in permissions.SAFE_METHODS:
            if hasattr(obj, 'tenant'):
                return obj.tenant == getattr(request, 'tenant', None)
            return True
        
        # Write permissions for superusers
        if request.user.is_superuser:
            return True
        
        # Write permissions for tenant admins in same tenant
        if request.user.role in ['admin', 'owner']:
            if hasattr(obj, 'tenant'):
                return obj.tenant == getattr(request, 'tenant', None)
            return True
        
        return False