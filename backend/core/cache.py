"""
Advanced caching utilities for MigrateIQ.

This module provides comprehensive caching functionality including:
- Query result caching
- API response caching
- Cache invalidation strategies
- Cache warming
- Distributed caching support
"""

import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union
from functools import wraps

from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.conf import settings
from django.db.models import Model
from django.http import HttpRequest, HttpResponse
from django.utils.cache import get_cache_key
from django.utils.encoding import force_str

import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class CacheManager:
    """Advanced cache manager with multiple strategies and monitoring."""
    
    def __init__(self):
        self.redis_client = self._get_redis_client()
        self.default_timeout = getattr(settings, 'CACHE_DEFAULT_TIMEOUT', 300)
        self.cache_prefix = getattr(settings, 'CACHE_KEY_PREFIX', 'migrateiq')
        
    def _get_redis_client(self):
        """Get Redis client for advanced operations."""
        try:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/1')
            return redis.from_url(redis_url, decode_responses=True)
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            return None
    
    def generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a consistent cache key from arguments."""
        key_parts = [self.cache_prefix, prefix]
        
        # Add positional arguments
        for arg in args:
            if isinstance(arg, (dict, list)):
                key_parts.append(hashlib.md5(json.dumps(arg, sort_keys=True).encode()).hexdigest())
            else:
                key_parts.append(str(arg))
        
        # Add keyword arguments
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            kwargs_str = json.dumps(sorted_kwargs, sort_keys=True)
            key_parts.append(hashlib.md5(kwargs_str.encode()).hexdigest())
        
        return ':'.join(key_parts)
    
    def get(self, key: str, default=None) -> Any:
        """Get value from cache with error handling."""
        try:
            return cache.get(key, default)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return default
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """Set value in cache with error handling."""
        try:
            timeout = timeout or self.default_timeout
            cache.set(key, value, timeout)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            cache.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern (Redis only)."""
        if not self.redis_client:
            logger.warning("Redis not available for pattern deletion")
            return 0
        
        try:
            keys = self.redis_client.keys(f"{self.cache_prefix}:{pattern}")
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except RedisError as e:
            logger.error(f"Redis pattern delete error: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            'cache_backend': settings.CACHES['default']['BACKEND'],
            'default_timeout': self.default_timeout,
            'redis_available': self.redis_client is not None
        }
        
        if self.redis_client:
            try:
                info = self.redis_client.info()
                stats.update({
                    'redis_memory_used': info.get('used_memory_human'),
                    'redis_connected_clients': info.get('connected_clients'),
                    'redis_total_commands': info.get('total_commands_processed'),
                    'redis_keyspace_hits': info.get('keyspace_hits'),
                    'redis_keyspace_misses': info.get('keyspace_misses'),
                })
                
                # Calculate hit rate
                hits = info.get('keyspace_hits', 0)
                misses = info.get('keyspace_misses', 0)
                total = hits + misses
                if total > 0:
                    stats['cache_hit_rate'] = round((hits / total) * 100, 2)
                
            except RedisError as e:
                logger.error(f"Error getting Redis stats: {e}")
        
        return stats


# Global cache manager instance
cache_manager = CacheManager()


def cache_result(timeout: Optional[int] = None, key_prefix: str = 'result'):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_manager.generate_cache_key(
                f"{key_prefix}:{func.__name__}", *args, **kwargs
            )
            
            # Try to get from cache
            result = cache_manager.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {func.__name__}")
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str):
    """Invalidate all cache keys matching pattern."""
    return cache_manager.delete_pattern(pattern)


def warm_cache(func, args_list: List[tuple], timeout: Optional[int] = None):
    """Warm cache by pre-computing results for given arguments."""
    warmed_count = 0
    
    for args in args_list:
        try:
            if isinstance(args, tuple):
                result = func(*args)
            else:
                result = func(args)
            warmed_count += 1
        except Exception as e:
            logger.error(f"Cache warming error for {func.__name__}: {e}")
    
    logger.info(f"Warmed {warmed_count} cache entries for {func.__name__}")
    return warmed_count


class ModelCacheInvalidator:
    """Automatic cache invalidation for model changes."""
    
    @staticmethod
    def invalidate_model_cache(model_class: Model, instance_id: Optional[int] = None):
        """Invalidate cache for a specific model."""
        model_name = model_class._meta.label_lower
        
        # Invalidate general model cache
        pattern = f"model:{model_name}:*"
        invalidate_cache_pattern(pattern)
        
        # Invalidate specific instance cache
        if instance_id:
            pattern = f"model:{model_name}:{instance_id}:*"
            invalidate_cache_pattern(pattern)
        
        logger.info(f"Invalidated cache for {model_name}")


class CacheMetrics:
    """Cache performance metrics collection."""
    
    @staticmethod
    def record_cache_hit(key: str):
        """Record a cache hit."""
        if cache_manager.redis_client:
            try:
                cache_manager.redis_client.incr(f"metrics:cache_hits:{key}")
            except RedisError:
                pass
    
    @staticmethod
    def record_cache_miss(key: str):
        """Record a cache miss."""
        if cache_manager.redis_client:
            try:
                cache_manager.redis_client.incr(f"metrics:cache_misses:{key}")
            except RedisError:
                pass
    
    @staticmethod
    def get_metrics() -> Dict[str, Any]:
        """Get cache metrics."""
        return cache_manager.get_cache_stats()


# Cache warming utilities
def warm_common_queries():
    """Warm cache with commonly accessed data."""
    from django.contrib.auth import get_user_model
    from core.models import Tenant
    
    User = get_user_model()
    
    # Warm user-related caches
    try:
        active_users = User.objects.filter(is_active=True)[:100]
        for user in active_users:
            cache_key = cache_manager.generate_cache_key('user', user.id)
            cache_manager.set(cache_key, user, 3600)  # 1 hour
        
        # Warm tenant caches
        active_tenants = Tenant.objects.filter(is_active=True)[:50]
        for tenant in active_tenants:
            cache_key = cache_manager.generate_cache_key('tenant', tenant.id)
            cache_manager.set(cache_key, tenant, 3600)  # 1 hour
        
        logger.info("Cache warming completed successfully")
        
    except Exception as e:
        logger.error(f"Cache warming failed: {e}")
