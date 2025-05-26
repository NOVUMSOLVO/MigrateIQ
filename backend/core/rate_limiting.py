"""
Enhanced rate limiting for MigrateIQ API.

This module provides advanced rate limiting functionality including:
- Per-user rate limiting
- Per-tenant rate limiting
- Dynamic rate limits based on subscription tiers
- Rate limit monitoring and analytics
"""

import time
import logging
from typing import Dict, Optional, Tuple
from django.core.cache import cache
from django.conf import settings
from django.http import HttpRequest
from rest_framework.throttling import BaseThrottle
from rest_framework.exceptions import Throttled
from django.utils import timezone
from datetime import timedelta
import hashlib
import json

logger = logging.getLogger(__name__)


class EnhancedRateLimitMixin:
    """Mixin for enhanced rate limiting functionality."""
    
    def get_rate_limit_key(self, request: HttpRequest, identifier: str, scope: str) -> str:
        """Generate a cache key for rate limiting."""
        key_parts = [
            'rate_limit',
            scope,
            identifier,
            self.get_cache_key_suffix(request)
        ]
        return ':'.join(key_parts)
    
    def get_cache_key_suffix(self, request: HttpRequest) -> str:
        """Get cache key suffix based on request."""
        # Include endpoint and method for granular rate limiting
        endpoint = request.path_info
        method = request.method
        return f"{method}:{endpoint}"
    
    def get_tenant_from_request(self, request: HttpRequest):
        """Extract tenant from request."""
        return getattr(request.user, 'tenant', None) if hasattr(request, 'user') and request.user.is_authenticated else None
    
    def get_subscription_tier(self, tenant) -> str:
        """Get subscription tier for tenant."""
        if not tenant:
            return 'free'
        return getattr(tenant, 'subscription_tier', 'free')


class UserRateThrottle(BaseThrottle, EnhancedRateLimitMixin):
    """Rate throttle per authenticated user with dynamic limits."""
    
    scope = 'user'
    
    # Default rate limits per subscription tier
    RATE_LIMITS = {
        'free': {'requests': 100, 'window': 3600},      # 100 requests per hour
        'basic': {'requests': 500, 'window': 3600},     # 500 requests per hour
        'premium': {'requests': 2000, 'window': 3600},  # 2000 requests per hour
        'enterprise': {'requests': 10000, 'window': 3600}, # 10000 requests per hour
    }
    
    # Endpoint-specific rate limits
    ENDPOINT_LIMITS = {
        '/api/ml/': {'multiplier': 0.5},  # ML endpoints are more expensive
        '/api/analyzer/': {'multiplier': 0.7},
        '/api/orchestrator/': {'multiplier': 0.8},
    }
    
    def allow_request(self, request: HttpRequest, view) -> bool:
        """Check if request should be allowed."""
        if not request.user.is_authenticated:
            return True  # Let anonymous throttle handle this
        
        user_id = str(request.user.id)
        tenant = self.get_tenant_from_request(request)
        subscription_tier = self.get_subscription_tier(tenant)
        
        # Get rate limit configuration
        rate_config = self.get_rate_limit_config(request, subscription_tier)
        
        # Check rate limit
        return self.check_rate_limit(request, user_id, rate_config)
    
    def get_rate_limit_config(self, request: HttpRequest, subscription_tier: str) -> Dict:
        """Get rate limit configuration for request."""
        base_config = self.RATE_LIMITS.get(subscription_tier, self.RATE_LIMITS['free'])
        
        # Apply endpoint-specific multipliers
        for endpoint, config in self.ENDPOINT_LIMITS.items():
            if request.path_info.startswith(endpoint):
                multiplier = config.get('multiplier', 1.0)
                return {
                    'requests': int(base_config['requests'] * multiplier),
                    'window': base_config['window']
                }
        
        return base_config
    
    def check_rate_limit(self, request: HttpRequest, identifier: str, rate_config: Dict) -> bool:
        """Check if request exceeds rate limit."""
        cache_key = self.get_rate_limit_key(request, identifier, self.scope)
        
        now = time.time()
        window = rate_config['window']
        limit = rate_config['requests']
        
        # Get current request count
        request_data = cache.get(cache_key, {'count': 0, 'reset_time': now + window})
        
        # Reset if window has expired
        if now >= request_data['reset_time']:
            request_data = {'count': 1, 'reset_time': now + window}
        else:
            request_data['count'] += 1
        
        # Update cache
        cache.set(cache_key, request_data, timeout=window)
        
        # Record metrics
        self.record_rate_limit_metrics(request, identifier, request_data['count'], limit)
        
        # Check if limit exceeded
        if request_data['count'] > limit:
            self.wait = request_data['reset_time'] - now
            return False
        
        return True
    
    def record_rate_limit_metrics(self, request: HttpRequest, identifier: str, current_count: int, limit: int):
        """Record rate limiting metrics."""
        metrics_key = f"rate_limit_metrics:{self.scope}:{identifier}"
        metrics = {
            'current_count': current_count,
            'limit': limit,
            'endpoint': request.path_info,
            'method': request.method,
            'timestamp': timezone.now().isoformat(),
            'utilization': (current_count / limit) * 100
        }
        
        # Store metrics for monitoring
        cache.set(metrics_key, metrics, timeout=3600)
        
        # Log high utilization
        if metrics['utilization'] > 80:
            logger.warning(f"High rate limit utilization for user {identifier}: {metrics['utilization']:.1f}%")


class TenantRateThrottle(BaseThrottle, EnhancedRateLimitMixin):
    """Rate throttle per tenant with quota management."""
    
    scope = 'tenant'
    
    # Tenant-level rate limits (higher than user limits)
    RATE_LIMITS = {
        'free': {'requests': 1000, 'window': 3600},      # 1000 requests per hour
        'basic': {'requests': 5000, 'window': 3600},     # 5000 requests per hour
        'premium': {'requests': 20000, 'window': 3600},  # 20000 requests per hour
        'enterprise': {'requests': 100000, 'window': 3600}, # 100000 requests per hour
    }
    
    def allow_request(self, request: HttpRequest, view) -> bool:
        """Check if request should be allowed."""
        tenant = self.get_tenant_from_request(request)
        if not tenant:
            return True  # No tenant, no limit
        
        tenant_id = str(tenant.id)
        subscription_tier = self.get_subscription_tier(tenant)
        
        # Get rate limit configuration
        rate_config = self.RATE_LIMITS.get(subscription_tier, self.RATE_LIMITS['free'])
        
        # Check rate limit
        return self.check_rate_limit(request, tenant_id, rate_config)
    
    def check_rate_limit(self, request: HttpRequest, identifier: str, rate_config: Dict) -> bool:
        """Check if request exceeds rate limit."""
        cache_key = self.get_rate_limit_key(request, identifier, self.scope)
        
        now = time.time()
        window = rate_config['window']
        limit = rate_config['requests']
        
        # Get current request count
        request_data = cache.get(cache_key, {'count': 0, 'reset_time': now + window})
        
        # Reset if window has expired
        if now >= request_data['reset_time']:
            request_data = {'count': 1, 'reset_time': now + window}
        else:
            request_data['count'] += 1
        
        # Update cache
        cache.set(cache_key, request_data, timeout=window)
        
        # Record metrics
        self.record_tenant_metrics(request, identifier, request_data['count'], limit)
        
        # Check if limit exceeded
        if request_data['count'] > limit:
            self.wait = request_data['reset_time'] - now
            return False
        
        return True
    
    def record_tenant_metrics(self, request: HttpRequest, identifier: str, current_count: int, limit: int):
        """Record tenant rate limiting metrics."""
        metrics_key = f"tenant_rate_metrics:{identifier}"
        metrics = {
            'current_count': current_count,
            'limit': limit,
            'endpoint': request.path_info,
            'method': request.method,
            'timestamp': timezone.now().isoformat(),
            'utilization': (current_count / limit) * 100
        }
        
        # Store metrics for monitoring
        cache.set(metrics_key, metrics, timeout=3600)
        
        # Log high utilization
        if metrics['utilization'] > 90:
            logger.warning(f"High tenant rate limit utilization for tenant {identifier}: {metrics['utilization']:.1f}%")


class DynamicRateThrottle(BaseThrottle, EnhancedRateLimitMixin):
    """Dynamic rate throttle that adjusts based on system load."""
    
    scope = 'dynamic'
    
    def allow_request(self, request: HttpRequest, view) -> bool:
        """Check if request should be allowed based on dynamic conditions."""
        # Get system load metrics
        system_load = self.get_system_load()
        
        # Adjust rate limits based on load
        if system_load > 0.9:  # High load
            multiplier = 0.5
        elif system_load > 0.7:  # Medium load
            multiplier = 0.7
        else:  # Normal load
            multiplier = 1.0
        
        # Apply dynamic rate limiting
        user_id = str(request.user.id) if request.user.is_authenticated else request.META.get('REMOTE_ADDR')
        base_limit = 100  # Base requests per hour
        adjusted_limit = int(base_limit * multiplier)
        
        rate_config = {'requests': adjusted_limit, 'window': 3600}
        return self.check_rate_limit(request, user_id, rate_config)
    
    def get_system_load(self) -> float:
        """Get current system load (simplified)."""
        # In a real implementation, this would check actual system metrics
        # For now, return a mock value
        load_key = 'system_load'
        return cache.get(load_key, 0.3)  # Default to 30% load
    
    def check_rate_limit(self, request: HttpRequest, identifier: str, rate_config: Dict) -> bool:
        """Check if request exceeds dynamic rate limit."""
        cache_key = self.get_rate_limit_key(request, identifier, self.scope)
        
        now = time.time()
        window = rate_config['window']
        limit = rate_config['requests']
        
        # Get current request count
        request_data = cache.get(cache_key, {'count': 0, 'reset_time': now + window})
        
        # Reset if window has expired
        if now >= request_data['reset_time']:
            request_data = {'count': 1, 'reset_time': now + window}
        else:
            request_data['count'] += 1
        
        # Update cache
        cache.set(cache_key, request_data, timeout=window)
        
        # Check if limit exceeded
        if request_data['count'] > limit:
            self.wait = request_data['reset_time'] - now
            return False
        
        return True


class RateLimitAnalytics:
    """Analytics for rate limiting."""
    
    @staticmethod
    def get_user_rate_limit_stats(user_id: str) -> Dict:
        """Get rate limit statistics for a user."""
        metrics_key = f"rate_limit_metrics:user:{user_id}"
        return cache.get(metrics_key, {})
    
    @staticmethod
    def get_tenant_rate_limit_stats(tenant_id: str) -> Dict:
        """Get rate limit statistics for a tenant."""
        metrics_key = f"tenant_rate_metrics:{tenant_id}"
        return cache.get(metrics_key, {})
    
    @staticmethod
    def get_global_rate_limit_stats() -> Dict:
        """Get global rate limiting statistics."""
        # This would aggregate stats from all users/tenants
        return {
            'total_requests': 0,
            'throttled_requests': 0,
            'average_utilization': 0.0,
            'peak_utilization': 0.0
        }


# Rate limiting configuration for different endpoints
ENDPOINT_RATE_LIMITS = {
    'default': {
        'user': UserRateThrottle,
        'tenant': TenantRateThrottle,
    },
    'high_cost': {
        'user': UserRateThrottle,
        'tenant': TenantRateThrottle,
        'dynamic': DynamicRateThrottle,
    }
}
