"""
Management command for rate limit operations.
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.cache import cache
from django.contrib.auth import get_user_model
from core.models import Tenant
from core.rate_limiting import RateLimitAnalytics
import json
from datetime import datetime, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Manage API rate limits'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['stats', 'reset', 'set-limit', 'monitor', 'export'],
            help='Action to perform'
        )
        
        parser.add_argument(
            '--user-id',
            type=str,
            help='User ID for user-specific operations'
        )
        
        parser.add_argument(
            '--tenant-id',
            type=str,
            help='Tenant ID for tenant-specific operations'
        )
        
        parser.add_argument(
            '--limit',
            type=int,
            help='New rate limit value'
        )
        
        parser.add_argument(
            '--window',
            type=int,
            default=3600,
            help='Time window in seconds (default: 3600)'
        )
        
        parser.add_argument(
            '--scope',
            choices=['user', 'tenant', 'global'],
            default='global',
            help='Scope for the operation'
        )
        
        parser.add_argument(
            '--output-file',
            type=str,
            help='Output file for export operations'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'stats':
            self.show_stats(options)
        elif action == 'reset':
            self.reset_limits(options)
        elif action == 'set-limit':
            self.set_limit(options)
        elif action == 'monitor':
            self.monitor_limits(options)
        elif action == 'export':
            self.export_stats(options)

    def show_stats(self, options):
        """Show rate limit statistics."""
        scope = options['scope']
        
        if scope == 'user':
            if options['user_id']:
                stats = RateLimitAnalytics.get_user_rate_limit_stats(options['user_id'])
                self.stdout.write(f"User {options['user_id']} rate limit stats:")
                self.stdout.write(json.dumps(stats, indent=2))
            else:
                self.stdout.write("Showing stats for all users:")
                self.show_all_user_stats()
        
        elif scope == 'tenant':
            if options['tenant_id']:
                stats = RateLimitAnalytics.get_tenant_rate_limit_stats(options['tenant_id'])
                self.stdout.write(f"Tenant {options['tenant_id']} rate limit stats:")
                self.stdout.write(json.dumps(stats, indent=2))
            else:
                self.stdout.write("Showing stats for all tenants:")
                self.show_all_tenant_stats()
        
        else:  # global
            stats = RateLimitAnalytics.get_global_rate_limit_stats()
            self.stdout.write("Global rate limit stats:")
            self.stdout.write(json.dumps(stats, indent=2))

    def show_all_user_stats(self):
        """Show rate limit stats for all users."""
        users = User.objects.filter(is_active=True)[:50]  # Limit to 50 users
        
        for user in users:
            stats = RateLimitAnalytics.get_user_rate_limit_stats(str(user.id))
            if stats:
                self.stdout.write(f"User {user.username} ({user.id}):")
                self.stdout.write(f"  Current: {stats.get('current_count', 0)}/{stats.get('limit', 0)}")
                self.stdout.write(f"  Utilization: {stats.get('utilization', 0):.1f}%")
                self.stdout.write("")

    def show_all_tenant_stats(self):
        """Show rate limit stats for all tenants."""
        tenants = Tenant.objects.filter(is_active=True)
        
        for tenant in tenants:
            stats = RateLimitAnalytics.get_tenant_rate_limit_stats(str(tenant.id))
            if stats:
                self.stdout.write(f"Tenant {tenant.name} ({tenant.id}):")
                self.stdout.write(f"  Current: {stats.get('current_count', 0)}/{stats.get('limit', 0)}")
                self.stdout.write(f"  Utilization: {stats.get('utilization', 0):.1f}%")
                self.stdout.write("")

    def reset_limits(self, options):
        """Reset rate limits."""
        scope = options['scope']
        
        if scope == 'user' and options['user_id']:
            # Reset specific user's rate limits
            cache_pattern = f"rate_limit:user:{options['user_id']}:*"
            self.clear_cache_pattern(cache_pattern)
            self.stdout.write(f"Reset rate limits for user {options['user_id']}")
        
        elif scope == 'tenant' and options['tenant_id']:
            # Reset specific tenant's rate limits
            cache_pattern = f"rate_limit:tenant:{options['tenant_id']}:*"
            self.clear_cache_pattern(cache_pattern)
            self.stdout.write(f"Reset rate limits for tenant {options['tenant_id']}")
        
        elif scope == 'global':
            # Reset all rate limits
            cache_pattern = "rate_limit:*"
            self.clear_cache_pattern(cache_pattern)
            self.stdout.write("Reset all rate limits")
        
        else:
            raise CommandError("Invalid scope or missing ID for reset operation")

    def clear_cache_pattern(self, pattern):
        """Clear cache keys matching pattern."""
        # This is a simplified implementation
        # In production, you'd use Redis SCAN or similar
        try:
            from django_redis import get_redis_connection
            redis_conn = get_redis_connection("default")
            keys = redis_conn.keys(pattern)
            if keys:
                redis_conn.delete(*keys)
                self.stdout.write(f"Cleared {len(keys)} cache keys")
        except ImportError:
            self.stdout.write("Redis not available, using cache.clear()")
            cache.clear()

    def set_limit(self, options):
        """Set custom rate limit."""
        if not options['limit']:
            raise CommandError("--limit is required for set-limit action")
        
        scope = options['scope']
        limit = options['limit']
        window = options['window']
        
        if scope == 'user' and options['user_id']:
            # Set custom limit for user
            cache_key = f"custom_rate_limit:user:{options['user_id']}"
            cache.set(cache_key, {'requests': limit, 'window': window}, timeout=86400)
            self.stdout.write(f"Set custom rate limit for user {options['user_id']}: {limit} requests per {window} seconds")
        
        elif scope == 'tenant' and options['tenant_id']:
            # Set custom limit for tenant
            cache_key = f"custom_rate_limit:tenant:{options['tenant_id']}"
            cache.set(cache_key, {'requests': limit, 'window': window}, timeout=86400)
            self.stdout.write(f"Set custom rate limit for tenant {options['tenant_id']}: {limit} requests per {window} seconds")
        
        else:
            raise CommandError("Invalid scope or missing ID for set-limit action")

    def monitor_limits(self, options):
        """Monitor rate limits in real-time."""
        self.stdout.write("Monitoring rate limits (press Ctrl+C to stop)...")
        
        try:
            import time
            while True:
                self.stdout.write(f"\n--- Rate Limit Monitor ({datetime.now()}) ---")
                
                # Show high utilization users
                self.show_high_utilization_users()
                
                # Show high utilization tenants
                self.show_high_utilization_tenants()
                
                time.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            self.stdout.write("\nMonitoring stopped.")

    def show_high_utilization_users(self):
        """Show users with high rate limit utilization."""
        users = User.objects.filter(is_active=True)[:100]
        high_util_users = []
        
        for user in users:
            stats = RateLimitAnalytics.get_user_rate_limit_stats(str(user.id))
            if stats and stats.get('utilization', 0) > 80:
                high_util_users.append((user, stats))
        
        if high_util_users:
            self.stdout.write("High utilization users:")
            for user, stats in high_util_users:
                self.stdout.write(f"  {user.username}: {stats['utilization']:.1f}% ({stats['current_count']}/{stats['limit']})")
        else:
            self.stdout.write("No high utilization users")

    def show_high_utilization_tenants(self):
        """Show tenants with high rate limit utilization."""
        tenants = Tenant.objects.filter(is_active=True)
        high_util_tenants = []
        
        for tenant in tenants:
            stats = RateLimitAnalytics.get_tenant_rate_limit_stats(str(tenant.id))
            if stats and stats.get('utilization', 0) > 90:
                high_util_tenants.append((tenant, stats))
        
        if high_util_tenants:
            self.stdout.write("High utilization tenants:")
            for tenant, stats in high_util_tenants:
                self.stdout.write(f"  {tenant.name}: {stats['utilization']:.1f}% ({stats['current_count']}/{stats['limit']})")
        else:
            self.stdout.write("No high utilization tenants")

    def export_stats(self, options):
        """Export rate limit statistics."""
        output_file = options.get('output_file', f'rate_limit_stats_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        
        # Collect all statistics
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'global_stats': RateLimitAnalytics.get_global_rate_limit_stats(),
            'user_stats': {},
            'tenant_stats': {}
        }
        
        # Export user stats
        users = User.objects.filter(is_active=True)
        for user in users:
            stats = RateLimitAnalytics.get_user_rate_limit_stats(str(user.id))
            if stats:
                export_data['user_stats'][str(user.id)] = {
                    'username': user.username,
                    'stats': stats
                }
        
        # Export tenant stats
        tenants = Tenant.objects.filter(is_active=True)
        for tenant in tenants:
            stats = RateLimitAnalytics.get_tenant_rate_limit_stats(str(tenant.id))
            if stats:
                export_data['tenant_stats'][str(tenant.id)] = {
                    'name': tenant.name,
                    'stats': stats
                }
        
        # Write to file
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.stdout.write(f"Exported rate limit statistics to {output_file}")
        self.stdout.write(f"Total users with stats: {len(export_data['user_stats'])}")
        self.stdout.write(f"Total tenants with stats: {len(export_data['tenant_stats'])}")
