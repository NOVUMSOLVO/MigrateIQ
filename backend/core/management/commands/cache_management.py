"""
Django management command for cache operations.

Usage:
    python manage.py cache_management --stats
    python manage.py cache_management --warm
    python manage.py cache_management --clear
    python manage.py cache_management --clear-pattern "api_response:*"
"""

import json
import time
from django.core.management.base import BaseCommand, CommandError
from django.core.cache import cache
from django.conf import settings

from core.cache import cache_manager, warm_common_queries, CacheMetrics


class Command(BaseCommand):
    help = 'Manage cache operations for MigrateIQ'

    def add_arguments(self, parser):
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show cache statistics',
        )
        parser.add_argument(
            '--warm',
            action='store_true',
            help='Warm cache with common queries',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all cache',
        )
        parser.add_argument(
            '--clear-pattern',
            type=str,
            help='Clear cache keys matching pattern',
        )
        parser.add_argument(
            '--test-cache',
            action='store_true',
            help='Test cache functionality',
        )
        parser.add_argument(
            '--monitor',
            action='store_true',
            help='Monitor cache performance in real-time',
        )

    def handle(self, *args, **options):
        if options['stats']:
            self.show_cache_stats()
        elif options['warm']:
            self.warm_cache()
        elif options['clear']:
            self.clear_cache()
        elif options['clear_pattern']:
            self.clear_cache_pattern(options['clear_pattern'])
        elif options['test_cache']:
            self.test_cache()
        elif options['monitor']:
            self.monitor_cache()
        else:
            self.stdout.write(
                self.style.ERROR('Please specify an action: --stats, --warm, --clear, --clear-pattern, --test-cache, or --monitor')
            )

    def show_cache_stats(self):
        """Display comprehensive cache statistics."""
        self.stdout.write(self.style.SUCCESS('=== Cache Statistics ==='))
        
        try:
            stats = cache_manager.get_cache_stats()
            
            self.stdout.write(f"Cache Backend: {stats.get('cache_backend', 'Unknown')}")
            self.stdout.write(f"Default Timeout: {stats.get('default_timeout')} seconds")
            self.stdout.write(f"Redis Available: {stats.get('redis_available', False)}")
            
            if stats.get('redis_available'):
                self.stdout.write("\n=== Redis Statistics ===")
                self.stdout.write(f"Memory Used: {stats.get('redis_memory_used', 'N/A')}")
                self.stdout.write(f"Connected Clients: {stats.get('redis_connected_clients', 'N/A')}")
                self.stdout.write(f"Total Commands: {stats.get('redis_total_commands', 'N/A')}")
                self.stdout.write(f"Keyspace Hits: {stats.get('redis_keyspace_hits', 'N/A')}")
                self.stdout.write(f"Keyspace Misses: {stats.get('redis_keyspace_misses', 'N/A')}")
                
                hit_rate = stats.get('cache_hit_rate')
                if hit_rate is not None:
                    color = self.style.SUCCESS if hit_rate > 80 else self.style.WARNING if hit_rate > 60 else self.style.ERROR
                    self.stdout.write(f"Cache Hit Rate: {color(f'{hit_rate}%')}")
            
            # Test cache connectivity
            test_key = 'cache_test_key'
            test_value = 'cache_test_value'
            cache.set(test_key, test_value, 60)
            retrieved_value = cache.get(test_key)
            
            if retrieved_value == test_value:
                self.stdout.write(self.style.SUCCESS("\n✓ Cache connectivity test passed"))
                cache.delete(test_key)
            else:
                self.stdout.write(self.style.ERROR("\n✗ Cache connectivity test failed"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error retrieving cache stats: {e}"))

    def warm_cache(self):
        """Warm cache with commonly accessed data."""
        self.stdout.write(self.style.SUCCESS('=== Warming Cache ==='))
        
        try:
            start_time = time.time()
            warm_common_queries()
            end_time = time.time()
            
            self.stdout.write(
                self.style.SUCCESS(f"✓ Cache warming completed in {end_time - start_time:.2f} seconds")
            )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Cache warming failed: {e}"))

    def clear_cache(self):
        """Clear all cache."""
        self.stdout.write(self.style.WARNING('=== Clearing All Cache ==='))
        
        try:
            cache.clear()
            self.stdout.write(self.style.SUCCESS("✓ All cache cleared successfully"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Cache clearing failed: {e}"))

    def clear_cache_pattern(self, pattern):
        """Clear cache keys matching pattern."""
        self.stdout.write(self.style.WARNING(f'=== Clearing Cache Pattern: {pattern} ==='))
        
        try:
            deleted_count = cache_manager.delete_pattern(pattern)
            self.stdout.write(
                self.style.SUCCESS(f"✓ Cleared {deleted_count} cache keys matching pattern '{pattern}'")
            )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Pattern cache clearing failed: {e}"))

    def test_cache(self):
        """Test cache functionality comprehensively."""
        self.stdout.write(self.style.SUCCESS('=== Testing Cache Functionality ==='))
        
        tests = [
            self._test_basic_operations,
            self._test_cache_manager,
            self._test_pattern_operations,
            self._test_cache_decorator,
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                test()
                passed += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Test failed: {e}"))
        
        if passed == total:
            self.stdout.write(self.style.SUCCESS(f"✓ All {total} tests passed"))
        else:
            self.stdout.write(self.style.ERROR(f"✗ {passed}/{total} tests passed"))

    def _test_basic_operations(self):
        """Test basic cache operations."""
        key = 'test_basic_key'
        value = {'test': 'data', 'number': 42}
        
        # Test set and get
        cache.set(key, value, 60)
        retrieved = cache.get(key)
        
        if retrieved != value:
            raise Exception("Basic set/get test failed")
        
        # Test delete
        cache.delete(key)
        if cache.get(key) is not None:
            raise Exception("Delete test failed")
        
        self.stdout.write("✓ Basic operations test passed")

    def _test_cache_manager(self):
        """Test cache manager functionality."""
        key = cache_manager.generate_cache_key('test', 'arg1', 'arg2', param='value')
        value = 'test_manager_value'
        
        # Test cache manager operations
        cache_manager.set(key, value, 60)
        retrieved = cache_manager.get(key)
        
        if retrieved != value:
            raise Exception("Cache manager test failed")
        
        cache_manager.delete(key)
        self.stdout.write("✓ Cache manager test passed")

    def _test_pattern_operations(self):
        """Test pattern-based operations."""
        if not cache_manager.redis_client:
            self.stdout.write("⚠ Skipping pattern test (Redis not available)")
            return
        
        # Set multiple keys with pattern
        pattern_keys = ['test_pattern:1', 'test_pattern:2', 'test_pattern:3']
        for key in pattern_keys:
            cache_manager.set(key, f'value_{key}', 60)
        
        # Delete by pattern
        deleted = cache_manager.delete_pattern('test_pattern:*')
        
        if deleted != len(pattern_keys):
            raise Exception(f"Pattern delete test failed: expected {len(pattern_keys)}, got {deleted}")
        
        self.stdout.write("✓ Pattern operations test passed")

    def _test_cache_decorator(self):
        """Test cache decorator functionality."""
        from core.cache import cache_result
        
        call_count = 0
        
        @cache_result(timeout=60, key_prefix='test_decorator')
        def test_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # First call should execute function
        result1 = test_function(1, 2)
        if result1 != 3 or call_count != 1:
            raise Exception("Decorator test failed on first call")
        
        # Second call should use cache
        result2 = test_function(1, 2)
        if result2 != 3 or call_count != 1:
            raise Exception("Decorator test failed on cached call")
        
        self.stdout.write("✓ Cache decorator test passed")

    def monitor_cache(self):
        """Monitor cache performance in real-time."""
        self.stdout.write(self.style.SUCCESS('=== Cache Performance Monitor ==='))
        self.stdout.write('Press Ctrl+C to stop monitoring\n')
        
        try:
            while True:
                stats = cache_manager.get_cache_stats()
                
                # Clear screen and show stats
                self.stdout.write('\033[2J\033[H')  # Clear screen
                self.stdout.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                if stats.get('redis_available'):
                    hit_rate = stats.get('cache_hit_rate', 0)
                    hits = stats.get('redis_keyspace_hits', 0)
                    misses = stats.get('redis_keyspace_misses', 0)
                    memory = stats.get('redis_memory_used', 'N/A')
                    clients = stats.get('redis_connected_clients', 0)
                    
                    self.stdout.write(f"Hit Rate: {hit_rate}%")
                    self.stdout.write(f"Hits: {hits}")
                    self.stdout.write(f"Misses: {misses}")
                    self.stdout.write(f"Memory Used: {memory}")
                    self.stdout.write(f"Connected Clients: {clients}")
                else:
                    self.stdout.write("Redis not available for detailed monitoring")
                
                time.sleep(5)  # Update every 5 seconds
                
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('\nMonitoring stopped'))
