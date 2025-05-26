"""
API versioning support for MigrateIQ.

This module provides:
- Header-based API versioning
- URL-based API versioning
- Backward compatibility management
- Version deprecation handling
"""

import logging
from typing import Dict, List, Optional, Tuple
from packaging import version

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework.versioning import BaseVersioning, URLPathVersioning, AcceptHeaderVersioning
from rest_framework.exceptions import NotAcceptable
from rest_framework import status

logger = logging.getLogger(__name__)


class APIVersioning(BaseVersioning):
    """
    Custom API versioning that supports multiple versioning schemes.
    
    Supports:
    - Header-based versioning (X-API-Version)
    - URL path versioning (/api/v1/)
    - Accept header versioning (application/vnd.migrateiq.v1+json)
    """
    
    default_version = '1.0'
    allowed_versions = ['1.0', '1.1', '2.0']
    version_param = 'version'
    
    def determine_version(self, request, *args, **kwargs):
        """Determine API version from request."""
        version_str = None
        
        # 1. Try header-based versioning first
        version_str = self._get_version_from_header(request)
        
        # 2. Try URL path versioning
        if not version_str:
            version_str = self._get_version_from_url(request)
        
        # 3. Try Accept header versioning
        if not version_str:
            version_str = self._get_version_from_accept_header(request)
        
        # 4. Use default version
        if not version_str:
            version_str = self.default_version
        
        # Validate version
        if version_str not in self.allowed_versions:
            raise NotAcceptable(
                f"Invalid API version '{version_str}'. "
                f"Supported versions: {', '.join(self.allowed_versions)}"
            )
        
        return version_str
    
    def _get_version_from_header(self, request: HttpRequest) -> Optional[str]:
        """Get version from X-API-Version header."""
        return request.META.get('HTTP_X_API_VERSION')
    
    def _get_version_from_url(self, request: HttpRequest) -> Optional[str]:
        """Get version from URL path like /api/v1/."""
        path_parts = request.path.strip('/').split('/')
        for part in path_parts:
            if part.startswith('v') and part[1:].replace('.', '').isdigit():
                return part[1:]  # Remove 'v' prefix
        return None
    
    def _get_version_from_accept_header(self, request: HttpRequest) -> Optional[str]:
        """Get version from Accept header like application/vnd.migrateiq.v1+json."""
        accept_header = request.META.get('HTTP_ACCEPT', '')
        if 'vnd.migrateiq.v' in accept_header:
            try:
                # Extract version from something like "application/vnd.migrateiq.v1+json"
                parts = accept_header.split('vnd.migrateiq.v')[1]
                version_part = parts.split('+')[0]
                return version_part
            except (IndexError, ValueError):
                pass
        return None
    
    def reverse(self, viewname, args=None, kwargs=None, request=None, format=None, **extra):
        """Reverse URL with version information."""
        if request and hasattr(request, 'version'):
            # Add version to URL if using URL-based versioning
            if 'v' + request.version not in viewname:
                viewname = f"v{request.version}:{viewname}"
        
        return super().reverse(viewname, args, kwargs, request, format, **extra)


class VersionCompatibilityMiddleware(MiddlewareMixin):
    """
    Middleware to handle API version compatibility and deprecation warnings.
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.deprecated_versions = getattr(settings, 'API_DEPRECATED_VERSIONS', ['1.0'])
        self.sunset_versions = getattr(settings, 'API_SUNSET_VERSIONS', {})
        
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Process request to check version compatibility."""
        # Skip non-API requests
        if not request.path.startswith('/api/'):
            return None
        
        # Get API version (will be set by versioning class)
        api_version = getattr(request, 'version', None)
        if not api_version:
            return None
        
        # Check if version is deprecated
        if api_version in self.deprecated_versions:
            logger.warning(f"Deprecated API version {api_version} used by {request.META.get('REMOTE_ADDR')}")
        
        return None
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Add version-related headers to response."""
        # Skip non-API requests
        if not request.path.startswith('/api/'):
            return response
        
        api_version = getattr(request, 'version', None)
        if not api_version:
            return response
        
        # Add version header
        response['X-API-Version'] = api_version
        
        # Add deprecation warning if applicable
        if api_version in self.deprecated_versions:
            response['Warning'] = f'299 - "API version {api_version} is deprecated"'
            response['Deprecation'] = 'true'
        
        # Add sunset date if applicable
        if api_version in self.sunset_versions:
            sunset_date = self.sunset_versions[api_version]
            response['Sunset'] = sunset_date
        
        # Add supported versions
        response['X-API-Supported-Versions'] = ', '.join(
            getattr(settings, 'API_SUPPORTED_VERSIONS', ['1.0', '1.1', '2.0'])
        )
        
        return response


class VersionedSerializer:
    """
    Base class for version-aware serializers.
    """
    
    def __init__(self, *args, **kwargs):
        self.version = kwargs.pop('version', '1.0')
        super().__init__(*args, **kwargs)
    
    def get_version_specific_fields(self) -> Dict[str, List[str]]:
        """
        Return version-specific field mappings.
        
        Example:
        {
            '1.0': ['field1', 'field2'],
            '1.1': ['field1', 'field2', 'field3'],
            '2.0': ['new_field1', 'new_field2']
        }
        """
        return {}
    
    def get_fields(self):
        """Get fields based on API version."""
        fields = super().get_fields()
        
        version_fields = self.get_version_specific_fields()
        if self.version in version_fields:
            # Filter fields based on version
            allowed_fields = version_fields[self.version]
            fields = {k: v for k, v in fields.items() if k in allowed_fields}
        
        return fields


class VersionedViewMixin:
    """
    Mixin for version-aware views.
    """
    
    def get_serializer_class(self):
        """Get serializer class based on API version."""
        serializer_class = super().get_serializer_class()
        
        # Check for version-specific serializer
        version_serializers = getattr(self, 'version_serializers', {})
        if hasattr(self.request, 'version') and self.request.version in version_serializers:
            serializer_class = version_serializers[self.request.version]
        
        return serializer_class
    
    def get_serializer(self, *args, **kwargs):
        """Get serializer instance with version information."""
        kwargs['version'] = getattr(self.request, 'version', '1.0')
        return super().get_serializer(*args, **kwargs)
    
    def get_queryset(self):
        """Get queryset with version-specific optimizations."""
        queryset = super().get_queryset()
        
        # Apply version-specific optimizations
        version_optimizations = getattr(self, 'version_optimizations', {})
        if hasattr(self.request, 'version') and self.request.version in version_optimizations:
            optimization = version_optimizations[self.request.version]
            if 'select_related' in optimization:
                queryset = queryset.select_related(*optimization['select_related'])
            if 'prefetch_related' in optimization:
                queryset = queryset.prefetch_related(*optimization['prefetch_related'])
        
        return queryset


class APIVersionManager:
    """
    Manager for API version lifecycle.
    """
    
    def __init__(self):
        self.versions = getattr(settings, 'API_VERSIONS', {
            '1.0': {
                'status': 'deprecated',
                'sunset_date': '2024-12-31',
                'description': 'Initial API version'
            },
            '1.1': {
                'status': 'stable',
                'description': 'Enhanced API with additional features'
            },
            '2.0': {
                'status': 'beta',
                'description': 'Major API redesign'
            }
        })
    
    def get_version_info(self, version_str: str) -> Dict:
        """Get information about a specific API version."""
        return self.versions.get(version_str, {})
    
    def get_supported_versions(self) -> List[str]:
        """Get list of supported API versions."""
        return [v for v, info in self.versions.items() 
                if info.get('status') != 'sunset']
    
    def get_deprecated_versions(self) -> List[str]:
        """Get list of deprecated API versions."""
        return [v for v, info in self.versions.items() 
                if info.get('status') == 'deprecated']
    
    def is_version_supported(self, version_str: str) -> bool:
        """Check if a version is supported."""
        return version_str in self.get_supported_versions()
    
    def get_latest_version(self) -> str:
        """Get the latest stable API version."""
        stable_versions = [v for v, info in self.versions.items() 
                          if info.get('status') == 'stable']
        if stable_versions:
            return max(stable_versions, key=lambda x: version.parse(x))
        return max(self.versions.keys(), key=lambda x: version.parse(x))
    
    def get_migration_path(self, from_version: str, to_version: str) -> List[Dict]:
        """Get migration path between versions."""
        # This would contain migration instructions
        # For now, return basic information
        return [
            {
                'from': from_version,
                'to': to_version,
                'breaking_changes': [],
                'new_features': [],
                'deprecated_features': []
            }
        ]


# Global version manager instance
version_manager = APIVersionManager()


def get_api_version_info():
    """Get comprehensive API version information."""
    return {
        'supported_versions': version_manager.get_supported_versions(),
        'deprecated_versions': version_manager.get_deprecated_versions(),
        'latest_version': version_manager.get_latest_version(),
        'version_details': version_manager.versions
    }
