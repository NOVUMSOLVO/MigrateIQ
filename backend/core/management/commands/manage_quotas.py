"""
Management command for tenant quota operations.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db.models import Count, Sum
from core.models import Tenant, TenantQuota, TenantUsage
from authentication.models import User
from projects.models import Project
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Manage tenant quotas and usage tracking'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['update', 'check', 'reset', 'report'],
            required=True,
            help='Action to perform'
        )
        parser.add_argument(
            '--tenant',
            type=str,
            help='Tenant slug (optional, applies to all tenants if not specified)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force operation without confirmation'
        )

    def handle(self, *args, **options):
        action = options['action']
        tenant_slug = options.get('tenant')
        force = options.get('force', False)

        try:
            if tenant_slug:
                tenants = [Tenant.objects.get(slug=tenant_slug)]
            else:
                tenants = Tenant.objects.filter(is_active=True)

            if action == 'update':
                self.update_quotas(tenants, force)
            elif action == 'check':
                self.check_quotas(tenants)
            elif action == 'reset':
                self.reset_quotas(tenants, force)
            elif action == 'report':
                self.generate_report(tenants)

        except Tenant.DoesNotExist:
            raise CommandError(f'Tenant "{tenant_slug}" does not exist')
        except Exception as e:
            logger.error(f'Error in quota management: {str(e)}')
            raise CommandError(f'Error: {str(e)}')

    def update_quotas(self, tenants, force=False):
        """Update quota usage for tenants."""
        self.stdout.write(f'Updating quotas for {len(tenants)} tenant(s)...')
        
        if not force:
            confirm = input('This will update quota usage. Continue? (y/N): ')
            if confirm.lower() != 'y':
                self.stdout.write('Operation cancelled.')
                return

        updated_count = 0
        for tenant in tenants:
            try:
                quota, created = TenantQuota.objects.get_or_create(tenant=tenant)
                
                # Update user count
                quota.current_users = User.objects.filter(tenant=tenant, is_active=True).count()
                
                # Update project count
                quota.current_projects = Project.objects.filter(tenant=tenant).count()
                
                # Update data source count (assuming you have a DataSource model)
                # quota.current_data_sources = DataSource.objects.filter(tenant=tenant).count()
                
                # Update storage usage (this would need to be calculated based on your storage logic)
                # quota.current_storage_gb = self.calculate_storage_usage(tenant)
                
                quota.save()
                updated_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(f'Updated quota for tenant: {tenant.name}')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to update quota for {tenant.name}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} tenant quotas')
        )

    def check_quotas(self, tenants):
        """Check quota limits for tenants."""
        self.stdout.write('Checking quota limits...\n')
        
        warnings = []
        violations = []
        
        for tenant in tenants:
            try:
                quota = TenantQuota.objects.get(tenant=tenant)
                
                # Check user limit
                if quota.is_user_limit_exceeded():
                    violations.append(f'{tenant.name}: User limit exceeded ({quota.current_users}/{tenant.max_users})')
                elif quota.current_users >= tenant.max_users * quota.user_warning_threshold:
                    warnings.append(f'{tenant.name}: User limit warning ({quota.current_users}/{tenant.max_users})')
                
                # Check storage limit
                if quota.is_storage_limit_exceeded():
                    violations.append(f'{tenant.name}: Storage limit exceeded ({quota.current_storage_gb:.2f}/{tenant.max_storage_gb} GB)')
                elif quota.current_storage_gb >= tenant.max_storage_gb * quota.storage_warning_threshold:
                    warnings.append(f'{tenant.name}: Storage limit warning ({quota.current_storage_gb:.2f}/{tenant.max_storage_gb} GB)')
                
                # Check API limit
                if quota.is_api_limit_exceeded():
                    violations.append(f'{tenant.name}: API limit exceeded ({quota.api_calls_this_hour}/{tenant.max_api_calls_per_hour} calls/hour)')
                
            except TenantQuota.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'No quota record found for tenant: {tenant.name}')
                )

        # Display results
        if violations:
            self.stdout.write(self.style.ERROR('QUOTA VIOLATIONS:'))
            for violation in violations:
                self.stdout.write(self.style.ERROR(f'  - {violation}'))
            self.stdout.write('')

        if warnings:
            self.stdout.write(self.style.WARNING('QUOTA WARNINGS:'))
            for warning in warnings:
                self.stdout.write(self.style.WARNING(f'  - {warning}'))
            self.stdout.write('')

        if not violations and not warnings:
            self.stdout.write(self.style.SUCCESS('All quotas are within limits'))

    def reset_quotas(self, tenants, force=False):
        """Reset API call counters for tenants."""
        self.stdout.write(f'Resetting API counters for {len(tenants)} tenant(s)...')
        
        if not force:
            confirm = input('This will reset API call counters. Continue? (y/N): ')
            if confirm.lower() != 'y':
                self.stdout.write('Operation cancelled.')
                return

        reset_count = 0
        for tenant in tenants:
            try:
                quota = TenantQuota.objects.get(tenant=tenant)
                quota.api_calls_today = 0
                quota.api_calls_this_hour = 0
                quota.last_api_call_reset = timezone.now()
                quota.save()
                
                reset_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Reset API counters for tenant: {tenant.name}')
                )
                
            except TenantQuota.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'No quota record found for tenant: {tenant.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully reset API counters for {reset_count} tenants')
        )

    def generate_report(self, tenants):
        """Generate quota usage report."""
        self.stdout.write('Generating quota usage report...\n')
        
        total_users = 0
        total_projects = 0
        total_storage = 0.0
        
        self.stdout.write(f'{"Tenant":<20} {"Users":<10} {"Projects":<10} {"Storage (GB)":<15} {"Status":<10}')
        self.stdout.write('-' * 70)
        
        for tenant in tenants:
            try:
                quota = TenantQuota.objects.get(tenant=tenant)
                
                # Determine status
                status = 'OK'
                if (quota.is_user_limit_exceeded() or 
                    quota.is_storage_limit_exceeded() or 
                    quota.is_api_limit_exceeded()):
                    status = 'VIOLATION'
                elif (quota.current_users >= tenant.max_users * quota.user_warning_threshold or
                      quota.current_storage_gb >= tenant.max_storage_gb * quota.storage_warning_threshold):
                    status = 'WARNING'
                
                self.stdout.write(
                    f'{tenant.name:<20} '
                    f'{quota.current_users}/{tenant.max_users:<10} '
                    f'{quota.current_projects}/{tenant.max_projects:<10} '
                    f'{quota.current_storage_gb:.1f}/{tenant.max_storage_gb:<15} '
                    f'{status:<10}'
                )
                
                total_users += quota.current_users
                total_projects += quota.current_projects
                total_storage += quota.current_storage_gb
                
            except TenantQuota.DoesNotExist:
                self.stdout.write(
                    f'{tenant.name:<20} {"N/A":<10} {"N/A":<10} {"N/A":<15} {"NO QUOTA":<10}'
                )
        
        self.stdout.write('-' * 70)
        self.stdout.write(
            f'{"TOTAL":<20} '
            f'{total_users:<10} '
            f'{total_projects:<10} '
            f'{total_storage:.1f} GB'
        )

    def calculate_storage_usage(self, tenant):
        """Calculate storage usage for a tenant."""
        # This is a placeholder - implement based on your storage logic
        # You might calculate based on file uploads, database size, etc.
        return 0.0
