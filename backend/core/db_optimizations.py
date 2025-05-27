"""
Database optimization utilities for MigrateIQ.
"""

from django.db import models, connection
from django.core.management.base import BaseCommand
from django.apps import apps
import logging

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """
    Utility class for database optimizations.
    """
    
    @staticmethod
    def create_indexes():
        """Create optimized indexes for better query performance."""
        with connection.cursor() as cursor:
            # Core models indexes
            indexes = [
                # Tenant and Domain indexes
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tenant_slug ON core_tenant(slug)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tenant_active ON core_tenant(is_active) WHERE is_active = true",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_domain_tenant ON core_domain(tenant_id)",
                
                # User indexes
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_tenant ON authentication_user(tenant_id)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_email_tenant ON authentication_user(email, tenant_id)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_role ON authentication_user(role)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_active ON authentication_user(is_active) WHERE is_active = true",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_last_login ON authentication_user(last_login)",
                
                # Project indexes
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_project_tenant ON orchestrator_migrationproject(tenant_id)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_project_status ON orchestrator_migrationproject(status)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_project_created ON orchestrator_migrationproject(created_at)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_project_updated ON orchestrator_migrationproject(updated_at)",
                
                # Migration Task indexes
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_task_project ON orchestrator_migrationtask(project_id)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_task_status ON orchestrator_migrationtask(status)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_task_created ON orchestrator_migrationtask(created_at)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_task_priority ON orchestrator_migrationtask(priority)",
                
                # Audit Log indexes
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_tenant ON core_auditlog(tenant_id)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_user ON core_auditlog(user_id)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_action ON core_auditlog(action)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_timestamp ON core_auditlog(timestamp)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_resource ON core_auditlog(resource_type, resource_id)",
                
                # Performance Log indexes
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_perf_operation ON monitoring_performancelog(operation_type)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_perf_timestamp ON monitoring_performancelog(timestamp)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_perf_duration ON monitoring_performancelog(duration_ms)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_perf_status ON monitoring_performancelog(status)",
                
                # System Metric indexes
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_metric_type ON monitoring_systemmetric(metric_type)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_metric_timestamp ON monitoring_systemmetric(timestamp)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_metric_tenant ON monitoring_systemmetric(tenant_id)",
                
                # Composite indexes for common queries
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_tenant_active ON authentication_user(tenant_id, is_active) WHERE is_active = true",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_project_tenant_status ON orchestrator_migrationproject(tenant_id, status)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_tenant_timestamp ON core_auditlog(tenant_id, timestamp)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_task_project_status ON orchestrator_migrationtask(project_id, status)",
            ]
            
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                    logger.info(f"Created index: {index_sql}")
                except Exception as e:
                    logger.warning(f"Failed to create index: {index_sql}. Error: {e}")
    
    @staticmethod
    def create_partial_indexes():
        """Create partial indexes for specific conditions."""
        with connection.cursor() as cursor:
            partial_indexes = [
                # Active records only
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_active_users ON authentication_user(id) WHERE is_active = true",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_active_tenants ON core_tenant(id) WHERE is_active = true",
                
                # Recent records
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_recent_audits ON core_auditlog(timestamp) WHERE timestamp > NOW() - INTERVAL '30 days'",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_recent_metrics ON monitoring_systemmetric(timestamp) WHERE timestamp > NOW() - INTERVAL '7 days'",
                
                # Failed tasks for retry
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_failed_tasks ON orchestrator_migrationtask(created_at) WHERE status = 'FAILED'",
                
                # In-progress projects
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_active_projects ON orchestrator_migrationproject(updated_at) WHERE status IN ('PLANNING', 'IN_PROGRESS')",
            ]
            
            for index_sql in partial_indexes:
                try:
                    cursor.execute(index_sql)
                    logger.info(f"Created partial index: {index_sql}")
                except Exception as e:
                    logger.warning(f"Failed to create partial index: {index_sql}. Error: {e}")
    
    @staticmethod
    def analyze_tables():
        """Update table statistics for better query planning."""
        with connection.cursor() as cursor:
            # Get all tables
            cursor.execute("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename LIKE 'core_%' 
                OR tablename LIKE 'authentication_%'
                OR tablename LIKE 'orchestrator_%'
                OR tablename LIKE 'monitoring_%'
                OR tablename LIKE 'analyzer_%'
                OR tablename LIKE 'ml_%'
                OR tablename LIKE 'validation_%'
                OR tablename LIKE 'transformation_%'
            """)
            
            tables = cursor.fetchall()
            for (table_name,) in tables:
                try:
                    cursor.execute(f"ANALYZE {table_name}")
                    logger.info(f"Analyzed table: {table_name}")
                except Exception as e:
                    logger.warning(f"Failed to analyze table {table_name}: {e}")
    
    @staticmethod
    def vacuum_tables():
        """Vacuum tables to reclaim space and update statistics."""
        with connection.cursor() as cursor:
            # Get tables that need vacuuming (high update/delete activity)
            high_activity_tables = [
                'core_auditlog',
                'monitoring_performancelog',
                'monitoring_systemmetric',
                'orchestrator_migrationtask',
                'authentication_usersession',
            ]
            
            for table_name in high_activity_tables:
                try:
                    cursor.execute(f"VACUUM ANALYZE {table_name}")
                    logger.info(f"Vacuumed table: {table_name}")
                except Exception as e:
                    logger.warning(f"Failed to vacuum table {table_name}: {e}")
    
    @staticmethod
    def get_slow_queries():
        """Get slow queries from pg_stat_statements if available."""
        with connection.cursor() as cursor:
            try:
                cursor.execute("""
                    SELECT 
                        query,
                        calls,
                        total_time,
                        mean_time,
                        rows
                    FROM pg_stat_statements 
                    WHERE mean_time > 1000  -- queries taking more than 1 second on average
                    ORDER BY mean_time DESC 
                    LIMIT 10
                """)
                
                slow_queries = cursor.fetchall()
                return slow_queries
            except Exception as e:
                logger.warning(f"Could not fetch slow queries: {e}")
                return []
    
    @staticmethod
    def get_table_sizes():
        """Get table sizes for monitoring."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """)
            
            return cursor.fetchall()
    
    @staticmethod
    def get_index_usage():
        """Get index usage statistics."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes 
                ORDER BY idx_scan DESC
            """)
            
            return cursor.fetchall()
    
    @staticmethod
    def optimize_connection_pool():
        """Optimize database connection pool settings."""
        optimizations = {
            'CONN_MAX_AGE': 300,  # 5 minutes
            'CONN_HEALTH_CHECKS': True,
            'OPTIONS': {
                'MAX_CONNS': 20,
                'MIN_CONNS': 5,
                'RETRY_ATTEMPTS': 3,
                'RETRY_DELAY': 1,
            }
        }
        return optimizations


class QueryOptimizer:
    """
    Query optimization utilities.
    """
    
    @staticmethod
    def get_optimized_queryset(model_class, filters=None, select_related=None, prefetch_related=None):
        """Get an optimized queryset for a model."""
        queryset = model_class.objects.all()
        
        if filters:
            queryset = queryset.filter(**filters)
        
        if select_related:
            queryset = queryset.select_related(*select_related)
        
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)
        
        return queryset
    
    @staticmethod
    def bulk_create_optimized(model_class, objects, batch_size=1000):
        """Optimized bulk create with batching."""
        created_objects = []
        for i in range(0, len(objects), batch_size):
            batch = objects[i:i + batch_size]
            created_objects.extend(
                model_class.objects.bulk_create(batch, ignore_conflicts=True)
            )
        return created_objects
    
    @staticmethod
    def bulk_update_optimized(objects, fields, batch_size=1000):
        """Optimized bulk update with batching."""
        model_class = objects[0].__class__
        for i in range(0, len(objects), batch_size):
            batch = objects[i:i + batch_size]
            model_class.objects.bulk_update(batch, fields)


# Common query optimizations for models
COMMON_OPTIMIZATIONS = {
    'authentication.User': {
        'select_related': ['tenant'],
        'prefetch_related': [],
    },
    'orchestrator.MigrationProject': {
        'select_related': ['tenant', 'created_by'],
        'prefetch_related': ['tasks'],
    },
    'orchestrator.MigrationTask': {
        'select_related': ['project', 'project__tenant'],
        'prefetch_related': [],
    },
    'core.AuditLog': {
        'select_related': ['tenant', 'user'],
        'prefetch_related': [],
    },
}
