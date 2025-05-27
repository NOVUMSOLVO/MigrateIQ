"""
Management command to optimize database performance.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from core.db_optimizations import DatabaseOptimizer
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Optimize database performance by creating indexes, analyzing tables, and running maintenance tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--indexes',
            action='store_true',
            help='Create optimized indexes',
        )
        parser.add_argument(
            '--partial-indexes',
            action='store_true',
            help='Create partial indexes',
        )
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='Analyze tables to update statistics',
        )
        parser.add_argument(
            '--vacuum',
            action='store_true',
            help='Vacuum tables to reclaim space',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all optimization tasks',
        )
        parser.add_argument(
            '--report',
            action='store_true',
            help='Generate performance report',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting database optimization...')
        )

        # Check if we're using PostgreSQL
        if 'postgresql' not in connection.vendor:
            raise CommandError('This command is designed for PostgreSQL databases only')

        optimizer = DatabaseOptimizer()

        if options['all'] or options['indexes']:
            self.stdout.write('Creating optimized indexes...')
            try:
                optimizer.create_indexes()
                self.stdout.write(
                    self.style.SUCCESS('✓ Indexes created successfully')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to create indexes: {e}')
                )

        if options['all'] or options['partial_indexes']:
            self.stdout.write('Creating partial indexes...')
            try:
                optimizer.create_partial_indexes()
                self.stdout.write(
                    self.style.SUCCESS('✓ Partial indexes created successfully')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to create partial indexes: {e}')
                )

        if options['all'] or options['analyze']:
            self.stdout.write('Analyzing tables...')
            try:
                optimizer.analyze_tables()
                self.stdout.write(
                    self.style.SUCCESS('✓ Tables analyzed successfully')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to analyze tables: {e}')
                )

        if options['all'] or options['vacuum']:
            self.stdout.write('Vacuuming tables...')
            try:
                optimizer.vacuum_tables()
                self.stdout.write(
                    self.style.SUCCESS('✓ Tables vacuumed successfully')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to vacuum tables: {e}')
                )

        if options['report']:
            self.generate_performance_report(optimizer)

        self.stdout.write(
            self.style.SUCCESS('Database optimization completed!')
        )

    def generate_performance_report(self, optimizer):
        """Generate a performance report."""
        self.stdout.write('\n' + '='*50)
        self.stdout.write('DATABASE PERFORMANCE REPORT')
        self.stdout.write('='*50)

        # Table sizes
        self.stdout.write('\nTable Sizes:')
        self.stdout.write('-' * 30)
        table_sizes = optimizer.get_table_sizes()
        for schema, table, size, size_bytes in table_sizes[:10]:  # Top 10 largest tables
            self.stdout.write(f'{table:<30} {size:>15}')

        # Index usage
        self.stdout.write('\nIndex Usage (Top 10):')
        self.stdout.write('-' * 40)
        index_usage = optimizer.get_index_usage()
        for schema, table, index, scans, reads, fetches in index_usage[:10]:
            self.stdout.write(f'{index:<30} Scans: {scans:>8} Reads: {reads:>10}')

        # Slow queries
        self.stdout.write('\nSlow Queries:')
        self.stdout.write('-' * 20)
        slow_queries = optimizer.get_slow_queries()
        if slow_queries:
            for query, calls, total_time, mean_time, rows in slow_queries:
                self.stdout.write(f'Mean time: {mean_time:.2f}ms, Calls: {calls}')
                self.stdout.write(f'Query: {query[:100]}...')
                self.stdout.write('')
        else:
            self.stdout.write('No slow queries found or pg_stat_statements not available')

        # Connection info
        self.stdout.write('\nDatabase Connection Info:')
        self.stdout.write('-' * 30)
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            self.stdout.write(f'PostgreSQL Version: {version}')

            cursor.execute("SELECT current_database()")
            db_name = cursor.fetchone()[0]
            self.stdout.write(f'Database: {db_name}')

            cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
            db_size = cursor.fetchone()[0]
            self.stdout.write(f'Database Size: {db_size}')

        self.stdout.write('\n' + '='*50)
