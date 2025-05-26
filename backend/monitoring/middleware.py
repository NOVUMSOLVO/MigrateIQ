import time
import logging
import json
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpRequest, HttpResponse
from .models import PerformanceLog

logger = logging.getLogger(__name__)


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """Middleware to monitor and log performance of API requests"""
    
    def process_request(self, request):
        """Store the start time of the request processing"""
        request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Calculate request duration and log performance data"""
        # Skip if no start_time (e.g., for middleware tests)
        if not hasattr(request, 'start_time'):
            return response
        
        # Calculate duration in milliseconds
        duration = (time.time() - request.start_time) * 1000
        
        # Skip static files and admin requests
        path = request.path_info.lstrip('/')
        if any(path.startswith(prefix) for prefix in ['static/', 'media/', 'admin/']):
            return response
        
        # Skip health check endpoints
        if 'health' in path.lower() and request.method == 'GET':
            return response
        
        # Determine status category
        status_code = response.status_code
        if 200 <= status_code < 300:
            status = 'success'
        elif 400 <= status_code < 500:
            status = 'client_error'
        elif 500 <= status_code < 600:
            status = 'server_error'
        else:
            status = 'unknown'
        
        # Get tenant from request if available
        tenant = getattr(request, 'tenant', None)
        
        # Get user from request if available
        user = getattr(request, 'user', None)
        user_id = str(user.id) if user and user.is_authenticated else None
        
        # Extract operation details from path
        path_parts = path.split('/')
        if len(path_parts) > 1:
            resource_type = path_parts[0] or 'root'
            resource_id = path_parts[1] if len(path_parts) > 1 and path_parts[1].strip() else None
        else:
            resource_type = path
            resource_id = None
        
        # Prepare metadata
        metadata = {
            'method': request.method,
            'path': request.path_info,
            'status_code': status_code,
            'user_id': user_id,
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'query_params': dict(request.GET.items()),
        }
        
        # Add response content type and size if available
        if hasattr(response, 'content'):
            metadata['response_size'] = len(response.content)
        
        content_type = response.get('Content-Type', '')
        metadata['content_type'] = content_type
        
        # For very slow requests, log at warning level
        if duration > 1000:  # More than 1 second
            logger.warning(
                f"Slow request: {request.method} {request.path_info} took {duration:.2f}ms"
            )
        
        # For extremely slow requests, log at error level
        if duration > 3000:  # More than 3 seconds
            logger.error(
                f"Very slow request: {request.method} {request.path_info} took {duration:.2f}ms"
            )
        
        # Create performance log entry
        try:
            # Determine operation name from path and method
            if len(path_parts) > 2 and path_parts[2]:
                operation = f"{request.method}_{path_parts[0]}_{path_parts[2]}"
            else:
                operation = f"{request.method}_{resource_type}"
            
            # Create the performance log
            PerformanceLog.objects.create(
                tenant=tenant,
                operation=operation,
                resource_type=resource_type,
                resource_id=resource_id,
                duration_ms=duration,
                status=status,
                metadata=metadata
            )
            
            # Update API request count for tenant
            if tenant:
                self._increment_tenant_api_count(tenant)
            
        except Exception as e:
            logger.error(f"Error logging performance data: {e}")
        
        # Add Server-Timing header for performance transparency
        response['Server-Timing'] = f"total;dur={duration:.2f}"
        
        return response
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
    
    def _increment_tenant_api_count(self, tenant):
        """Increment API request count for tenant"""
        try:
            # Daily counter key
            today = timezone.now().date().isoformat()
            daily_key = f"tenant:{tenant.id}:api_requests:{today}"
            
            # Increment daily counter
            cache.incr(daily_key, 1)
            
            # Set expiry if new key
            if cache.ttl(daily_key) < 0:
                cache.expire(daily_key, 60*60*24*2)  # 2 days
            
            # 30-day rolling counter
            rolling_key = f"tenant:{tenant.id}:api_requests:30d"
            cache.incr(rolling_key, 1)
            
            # Set expiry if new key
            if cache.ttl(rolling_key) < 0:
                cache.expire(rolling_key, 60*60*24*31)  # 31 days
        
        except Exception as e:
            logger.error(f"Error incrementing tenant API count: {e}")


class PrometheusMetricsMiddleware(MiddlewareMixin):
    """Middleware to collect and expose Prometheus metrics"""
    
    def process_request(self, request):
        """Process incoming request for metrics collection"""
        request.prometheus_start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Process response for metrics collection"""
        if not hasattr(request, 'prometheus_start_time'):
            return response
        
        # Skip if django_prometheus is not installed
        try:
            from django_prometheus.exports import ExportToDjangoView
        except ImportError:
            return response
        
        # Skip metrics endpoint itself to avoid recursion
        if request.path_info.startswith('/metrics'):
            return response
        
        # Calculate request duration
        duration = time.time() - request.prometheus_start_time
        
        # Get tenant from request if available
        tenant_id = 'none'
        if hasattr(request, 'tenant') and request.tenant:
            tenant_id = str(request.tenant.id)
        
        # Get path for grouping similar URLs
        path = request.path_info
        
        # Skip static files and admin requests
        if any(path.startswith(prefix) for prefix in ['/static/', '/media/', '/admin/']):
            return response
        
        try:
            # Import prometheus client if available
            from prometheus_client import Counter, Histogram
            
            # Define metrics (these would normally be defined at module level)
            # but we're doing it here for demonstration
            REQUEST_COUNTER = Counter(
                'migrateiq_http_requests_total',
                'Total HTTP requests',
                ['method', 'path', 'status', 'tenant']
            )
            
            REQUEST_LATENCY = Histogram(
                'migrateiq_http_request_duration_seconds',
                'HTTP request latency in seconds',
                ['method', 'path', 'status', 'tenant'],
                buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, 25.0, 50.0, 75.0, float('inf'))
            )
            
            # Update metrics
            REQUEST_COUNTER.labels(
                method=request.method,
                path=path,
                status=str(response.status_code),
                tenant=tenant_id
            ).inc()
            
            REQUEST_LATENCY.labels(
                method=request.method,
                path=path,
                status=str(response.status_code),
                tenant=tenant_id
            ).observe(duration)
            
        except (ImportError, Exception) as e:
            logger.error(f"Error collecting Prometheus metrics: {e}")
        
        return response


class AuditLogMiddleware(MiddlewareMixin):
    """Middleware to log audit events for security and compliance"""
    
    SENSITIVE_PATHS = [
        '/api/auth/',
        '/api/users/',
        '/api/tenants/',
        '/api/admin/',
        '/api/settings/',
    ]
    
    def process_request(self, request):
        """Process request for audit logging"""
        # Store original request body for later use
        if self._should_log_request(request):
            try:
                request._body = request.body.decode('utf-8')
            except:
                request._body = '[binary data]'
        return None
    
    def process_response(self, request, response):
        """Log audit events based on request and response"""
        if not self._should_log_request(request):
            return response
        
        # Get user information
        user = getattr(request, 'user', None)
        user_id = str(user.id) if user and user.is_authenticated else 'anonymous'
        username = user.username if user and user.is_authenticated else 'anonymous'
        
        # Get tenant information
        tenant = getattr(request, 'tenant', None)
        tenant_id = str(tenant.id) if tenant else 'none'
        tenant_name = tenant.name if tenant else 'none'
        
        # Prepare audit log entry
        audit_data = {
            'timestamp': timezone.now().isoformat(),
            'user_id': user_id,
            'username': username,
            'tenant_id': tenant_id,
            'tenant_name': tenant_name,
            'ip_address': self._get_client_ip(request),
            'method': request.method,
            'path': request.path_info,
            'query_params': dict(request.GET.items()),
            'status_code': response.status_code,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        
        # Add request body for sensitive operations (POST, PUT, PATCH, DELETE)
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE'] and hasattr(request, '_body'):
            # Sanitize sensitive data
            body = self._sanitize_sensitive_data(request._body)
            audit_data['request_body'] = body
        
        # Log the audit event
        logger.info(f"AUDIT: {json.dumps(audit_data)}")
        
        return response
    
    def _should_log_request(self, request):
        """Determine if this request should be logged for audit purposes"""
        # Skip static files, media, and metrics
        path = request.path_info
        if any(path.startswith(prefix) for prefix in ['/static/', '/media/', '/metrics']):
            return False
        
        # Always log sensitive paths
        if any(path.startswith(prefix) for prefix in self.SENSITIVE_PATHS):
            return True
        
        # Log all write operations
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return True
        
        # Skip other GET requests
        return False
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
    
    def _sanitize_sensitive_data(self, data):
        """Sanitize sensitive data in request body"""
        if not data or data == '[binary data]':
            return data
        
        try:
            # Try to parse as JSON
            json_data = json.loads(data)
            
            # List of sensitive fields to redact
            sensitive_fields = [
                'password', 'token', 'secret', 'key', 'auth', 
                'credential', 'credit_card', 'card_number', 'cvv',
                'ssn', 'social_security', 'birth_date', 'dob'
            ]
            
            # Recursively sanitize the data
            def sanitize_dict(d):
                for k, v in d.items():
                    if isinstance(v, dict):
                        sanitize_dict(v)
                    elif isinstance(v, list):
                        for item in v:
                            if isinstance(item, dict):
                                sanitize_dict(item)
                    elif any(sensitive in k.lower() for sensitive in sensitive_fields):
                        d[k] = '******'
            
            if isinstance(json_data, dict):
                sanitize_dict(json_data)
                return json.dumps(json_data)
            
            return data
        
        except (json.JSONDecodeError, Exception):
            # If not JSON or error occurs, return as is
            return data