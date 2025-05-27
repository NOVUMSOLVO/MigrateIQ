"""
API Response Caching Middleware for MigrateIQ.

This middleware provides intelligent caching of API responses with:
- Configurable cache durations per endpoint
- Cache invalidation on data changes
- Compression support
- Cache headers management
"""

import json
import logging
import time
from typing import Dict, List, Optional

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.cache import get_cache_key, learn_cache_key, patch_response_headers
from django.utils.deprecation import MiddlewareMixin

from .cache import cache_manager, CacheMetrics

logger = logging.getLogger(__name__)


class APIResponseCacheMiddleware(MiddlewareMixin):
    """
    Middleware for caching API responses with intelligent invalidation.
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.cache_timeout = getattr(settings, 'API_CACHE_TIMEOUT', 300)  # 5 minutes default
        self.cacheable_methods = ['GET', 'HEAD']
        self.cache_headers = getattr(settings, 'API_CACHE_HEADERS', True)
        
        # Configure cache durations per endpoint pattern
        self.endpoint_cache_config = getattr(settings, 'API_CACHE_CONFIG', {
            '/api/projects/': 600,      # 10 minutes
            '/api/analyzer/': 1800,     # 30 minutes
            '/api/validation/': 300,    # 5 minutes
            '/api/ml/': 3600,          # 1 hour
            '/api/core/': 300,         # 5 minutes
        })
        
        # Endpoints that should never be cached
        self.no_cache_patterns = [
            '/api/auth/',
            '/api/admin/',
            '/api/health/',
        ]
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Check if we have a cached response for this request."""
        if not self._should_cache_request(request):
            return None
        
        cache_key = self._get_cache_key(request)
        if not cache_key:
            return None
        
        # Try to get cached response
        cached_response = cache_manager.get(cache_key)
        if cached_response:
            CacheMetrics.record_cache_hit(cache_key)
            logger.debug(f"Cache hit for {request.path}")
            
            # Reconstruct HttpResponse from cached data
            response = JsonResponse(
                cached_response['content'],
                status=cached_response['status_code'],
                safe=False
            )
            
            # Add cache headers
            if self.cache_headers:
                response['X-Cache'] = 'HIT'
                response['X-Cache-Key'] = cache_key
                response['Cache-Control'] = f'max-age={self.cache_timeout}'
            
            return response
        
        CacheMetrics.record_cache_miss(cache_key)
        return None
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Cache the response if appropriate."""
        if not self._should_cache_response(request, response):
            return response
        
        cache_key = self._get_cache_key(request)
        if not cache_key:
            return response
        
        # Prepare response data for caching
        try:
            if hasattr(response, 'content'):
                content = json.loads(response.content.decode('utf-8'))
            else:
                content = None
            
            cached_data = {
                'content': content,
                'status_code': response.status_code,
                'headers': dict(response.items()),
                'cached_at': time.time(),
            }
            
            # Get cache timeout for this endpoint
            timeout = self._get_cache_timeout(request.path)
            
            # Cache the response
            cache_manager.set(cache_key, cached_data, timeout)
            
            # Add cache headers
            if self.cache_headers:
                response['X-Cache'] = 'MISS'
                response['X-Cache-Key'] = cache_key
                response['Cache-Control'] = f'max-age={timeout}'
                response['Expires'] = time.strftime(
                    '%a, %d %b %Y %H:%M:%S GMT',
                    time.gmtime(time.time() + timeout)
                )
            
            logger.debug(f"Cached response for {request.path} (timeout: {timeout}s)")
            
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f"Failed to cache response for {request.path}: {e}")
        
        return response
    
    def _should_cache_request(self, request: HttpRequest) -> bool:
        """Determine if this request should be cached."""
        # Only cache safe methods
        if request.method not in self.cacheable_methods:
            return False
        
        # Don't cache if user is authenticated and this affects response
        if request.user.is_authenticated and self._is_user_specific_endpoint(request.path):
            return False
        
        # Check no-cache patterns
        for pattern in self.no_cache_patterns:
            if request.path.startswith(pattern):
                return False
        
        # Only cache API endpoints
        if not request.path.startswith('/api/'):
            return False
        
        return True
    
    def _should_cache_response(self, request: HttpRequest, response: HttpResponse) -> bool:
        """Determine if this response should be cached."""
        # Only cache successful responses
        if response.status_code not in [200, 201]:
            return False
        
        # Don't cache if response has cache-control no-cache
        cache_control = response.get('Cache-Control', '')
        if 'no-cache' in cache_control or 'no-store' in cache_control:
            return False
        
        # Check if response is JSON
        content_type = response.get('Content-Type', '')
        if 'application/json' not in content_type:
            return False
        
        return True
    
    def _get_cache_key(self, request: HttpRequest) -> Optional[str]:
        """Generate cache key for the request."""
        try:
            # Include query parameters in cache key
            query_params = sorted(request.GET.items())
            query_string = '&'.join([f"{k}={v}" for k, v in query_params])
            
            # Include user ID for user-specific endpoints
            user_id = request.user.id if request.user.is_authenticated else 'anonymous'
            
            cache_key = cache_manager.generate_cache_key(
                'api_response',
                request.path,
                query_string,
                user_id,
                request.method
            )
            
            return cache_key
            
        except Exception as e:
            logger.error(f"Error generating cache key: {e}")
            return None
    
    def _get_cache_timeout(self, path: str) -> int:
        """Get cache timeout for specific endpoint."""
        for pattern, timeout in self.endpoint_cache_config.items():
            if path.startswith(pattern):
                return timeout
        return self.cache_timeout
    
    def _is_user_specific_endpoint(self, path: str) -> bool:
        """Check if endpoint returns user-specific data."""
        user_specific_patterns = [
            '/api/projects/',  # User's projects
            '/api/core/profile/',  # User profile
            '/api/core/notifications/',  # User notifications
        ]
        
        for pattern in user_specific_patterns:
            if path.startswith(pattern):
                return True
        return False


class CacheInvalidationMiddleware(MiddlewareMixin):
    """
    Middleware to invalidate cache on data modifications.
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.invalidation_methods = ['POST', 'PUT', 'PATCH', 'DELETE']
        
        # Map endpoints to cache patterns to invalidate
        self.invalidation_patterns = {
            '/api/projects/': ['api_response:/api/projects/*'],
            '/api/analyzer/': ['api_response:/api/analyzer/*'],
            '/api/validation/': ['api_response:/api/validation/*'],
            '/api/ml/': ['api_response:/api/ml/*'],
        }
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Invalidate cache after successful modifications."""
        if (request.method in self.invalidation_methods and 
            response.status_code in [200, 201, 204]):
            
            self._invalidate_related_cache(request.path)
        
        return response
    
    def _invalidate_related_cache(self, path: str):
        """Invalidate cache patterns related to the modified endpoint."""
        for pattern, cache_patterns in self.invalidation_patterns.items():
            if path.startswith(pattern):
                for cache_pattern in cache_patterns:
                    invalidated = cache_manager.delete_pattern(cache_pattern)
                    logger.info(f"Invalidated {invalidated} cache entries for pattern: {cache_pattern}")


class CompressionMiddleware(MiddlewareMixin):
    """
    Middleware to compress API responses.
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.min_length = getattr(settings, 'COMPRESSION_MIN_LENGTH', 1024)
        self.compressible_types = [
            'application/json',
            'text/plain',
            'text/html',
            'application/javascript',
            'text/css',
        ]
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Compress response if appropriate."""
        if not self._should_compress(request, response):
            return response
        
        # Check if client accepts compression
        accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')
        
        if 'gzip' in accept_encoding:
            try:
                import gzip
                compressed_content = gzip.compress(response.content)
                
                # Only use compression if it actually reduces size
                if len(compressed_content) < len(response.content):
                    response.content = compressed_content
                    response['Content-Encoding'] = 'gzip'
                    response['Content-Length'] = str(len(compressed_content))
                    response['Vary'] = 'Accept-Encoding'
                    
            except Exception as e:
                logger.error(f"Compression error: {e}")
        
        return response
    
    def _should_compress(self, request: HttpRequest, response: HttpResponse) -> bool:
        """Determine if response should be compressed."""
        # Don't compress small responses
        if len(response.content) < self.min_length:
            return False
        
        # Don't compress if already compressed
        if response.get('Content-Encoding'):
            return False
        
        # Only compress specific content types
        content_type = response.get('Content-Type', '').split(';')[0]
        return content_type in self.compressible_types
