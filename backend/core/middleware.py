from django.utils.deprecation import MiddlewareMixin
from django.http import Http404, HttpResponse
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _, activate
from django.core.cache import cache
from django.conf import settings
from .models import Tenant, Domain, AuditLog
import threading
import json
import time
import logging

User = get_user_model()

# Thread-local storage for tenant
_thread_locals = threading.local()


def get_current_tenant():
    """Get the current tenant from thread-local storage."""
    return getattr(_thread_locals, 'tenant', None)


def set_current_tenant(tenant):
    """Set the current tenant in thread-local storage."""
    _thread_locals.tenant = tenant


class TenantMiddleware(MiddlewareMixin):
    """Middleware to handle multi-tenancy based on domain."""

    def process_request(self, request):
        """Process the request to determine the tenant."""
        host = request.get_host().split(':')[0]  # Remove port if present

        try:
            # Try to find tenant by domain
            domain = Domain.objects.select_related('tenant').get(
                domain=host,
                tenant__is_active=True
            )
            tenant = domain.tenant
        except Domain.DoesNotExist:
            # For development, allow localhost without tenant
            if host in ['localhost', '127.0.0.1', 'testserver']:
                # Create or get default tenant for development
                tenant, created = Tenant.objects.get_or_create(
                    slug='default',
                    defaults={
                        'name': 'Default Tenant',
                        'description': 'Default tenant for development',
                    }
                )
                if created:
                    Domain.objects.create(
                        tenant=tenant,
                        domain=host,
                        is_primary=True
                    )
            else:
                raise Http404(_("Tenant not found for domain: {}").format(host))

        # Set tenant in thread-local storage
        set_current_tenant(tenant)
        request.tenant = tenant

        return None

    def process_response(self, request, response):
        """Clean up thread-local storage."""
        if hasattr(_thread_locals, 'tenant'):
            delattr(_thread_locals, 'tenant')
        return response


class AuditMiddleware(MiddlewareMixin):
    """Middleware to log user actions for audit purposes."""

    # Actions to audit
    AUDIT_ACTIONS = {
        'POST': 'create',
        'PUT': 'update',
        'PATCH': 'update',
        'DELETE': 'delete',
    }

    # Paths to exclude from auditing
    EXCLUDE_PATHS = [
        '/api/health/',
        '/admin/jsi18n/',
        '/static/',
        '/media/',
    ]

    def process_request(self, request):
        """Store request data for later use in response processing."""
        # Skip if path should be excluded
        if any(request.path.startswith(path) for path in self.EXCLUDE_PATHS):
            return None

        # Store original request body for audit
        if hasattr(request, 'body'):
            try:
                request._audit_body = json.loads(request.body) if request.body else {}
            except (json.JSONDecodeError, UnicodeDecodeError):
                request._audit_body = {}

        return None

    def process_response(self, request, response):
        """Log the action if it should be audited."""
        # Skip if path should be excluded
        if any(request.path.startswith(path) for path in self.EXCLUDE_PATHS):
            return response

        # Only audit certain HTTP methods
        if request.method not in self.AUDIT_ACTIONS:
            return response

        # Only audit successful responses
        if response.status_code >= 400:
            return response

        # Get tenant and user
        tenant = getattr(request, 'tenant', None)
        user = request.user if request.user.is_authenticated else None

        # Extract resource information from path
        resource_type, resource_id = self._extract_resource_info(request.path)

        # Prepare audit data
        audit_data = {
            'tenant': tenant,
            'user': user,
            'action': self.AUDIT_ACTIONS[request.method],
            'resource_type': resource_type,
            'resource_id': resource_id,
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'metadata': {
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
            }
        }

        # Add request body for create/update actions
        if hasattr(request, '_audit_body') and request.method in ['POST', 'PUT', 'PATCH']:
            audit_data['changes'] = request._audit_body

        # Create audit log entry asynchronously
        try:
            AuditLog.objects.create(**audit_data)
        except Exception:
            # Don't fail the request if audit logging fails
            pass

        return response

    def _extract_resource_info(self, path):
        """Extract resource type and ID from the request path."""
        parts = [p for p in path.split('/') if p]

        if len(parts) >= 2 and parts[0] == 'api':
            resource_type = parts[1]
            resource_id = parts[2] if len(parts) > 2 and parts[2].isdigit() else None
            return resource_type, resource_id

        return 'unknown', None

    def _get_client_ip(self, request):
        """Get the client IP address from the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers to all responses.
    """

    def process_response(self, request, response):
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self' wss: ws:; "
            "frame-ancestors 'none';"
        )

        # X-Frame-Options
        response['X-Frame-Options'] = 'DENY'

        # X-Content-Type-Options
        response['X-Content-Type-Options'] = 'nosniff'

        # X-XSS-Protection
        response['X-XSS-Protection'] = '1; mode=block'

        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions Policy
        response['Permissions-Policy'] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "speaker=()"
        )

        # HTTPS enforcement in production
        if not settings.DEBUG:
            # HTTP Strict Transport Security
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'

            # Secure cookies
            response['Set-Cookie'] = response.get('Set-Cookie', '').replace(
                'HttpOnly', 'HttpOnly; Secure; SameSite=Strict'
            )

        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Advanced rate limiting middleware with different limits for different endpoints.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

    def process_request(self, request):
        # Skip rate limiting for certain paths
        skip_paths = ['/health/', '/metrics/', '/admin/']
        if any(request.path.startswith(path) for path in skip_paths):
            return None

        # Get client IP
        client_ip = self.get_client_ip(request)

        # Different rate limits for different endpoints
        rate_limits = self.get_rate_limits(request)

        for limit_type, (limit, window) in rate_limits.items():
            cache_key = f"rate_limit:{limit_type}:{client_ip}"

            # Get current count
            current_count = cache.get(cache_key, 0)

            if current_count >= limit:
                logger.warning(
                    f"Rate limit exceeded for {client_ip} on {request.path}. "
                    f"Limit: {limit}/{window}s"
                )
                response = HttpResponse(
                    "Rate limit exceeded. Please try again later.",
                    status=429
                )
                return response

            # Increment counter
            cache.set(cache_key, current_count + 1, window)

        return None

    def get_client_ip(self, request):
        """Get the client's IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get_rate_limits(self, request):
        """Get rate limits based on the request path and user."""
        limits = {}

        # Authentication endpoints - stricter limits
        if request.path.startswith('/api/auth/'):
            limits['auth'] = (10, 300)  # 10 requests per 5 minutes

        # API endpoints - general limits
        elif request.path.startswith('/api/'):
            if request.user.is_authenticated:
                limits['api_user'] = (1000, 3600)  # 1000 requests per hour for authenticated users
            else:
                limits['api_anon'] = (100, 3600)  # 100 requests per hour for anonymous users

        # File upload endpoints - special limits
        elif 'upload' in request.path:
            limits['upload'] = (20, 3600)  # 20 uploads per hour

        # Default limit
        else:
            limits['general'] = (200, 3600)  # 200 requests per hour

        return limits


class LocaleMiddleware(MiddlewareMixin):
    """
    Middleware to handle user language preferences.
    """

    def process_request(self, request):
        # Get language from user preferences if authenticated
        if request.user.is_authenticated and hasattr(request.user, 'language'):
            language = request.user.language
        else:
            # Get language from Accept-Language header
            language = request.META.get('HTTP_ACCEPT_LANGUAGE', 'en')
            if language:
                language = language.split(',')[0].split('-')[0]  # Get primary language

        # Validate language is supported
        supported_languages = [lang[0] for lang in settings.LANGUAGES]
        if language not in supported_languages:
            language = settings.LANGUAGE_CODE

        # Activate language
        activate(language)
        request.LANGUAGE_CODE = language

        return None