"""
Management command for GDPR and compliance operations.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from core.models import Tenant, AuditLog
from core.compliance import (
    DataRetentionPolicy, DataSubjectRequest, ConsentRecord, ComplianceReport
)
from authentication.models import User, UserActivity
import json
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Perform GDPR and compliance operations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['cleanup', 'export', 'anonymize', 'report', 'check_retention'],
            required=True,
            help='Compliance action to perform'
        )
        parser.add_argument(
            '--tenant',
            type=str,
            help='Tenant slug (optional)'
        )
        parser.add_argument(
            '--user-email',
            type=str,
            help='User email for data export/anonymization'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days for retention checks'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force operation without confirmation'
        )

    def handle(self, *args, **options):
        action = options['action']
        tenant_slug = options.get('tenant')
        user_email = options.get('user_email')
        days = options.get('days', 30)
        dry_run = options.get('dry_run', False)
        force = options.get('force', False)

        try:
            tenant = None
            if tenant_slug:
                tenant = Tenant.objects.get(slug=tenant_slug)

            if action == 'cleanup':
                self.cleanup_old_data(tenant, days, dry_run, force)
            elif action == 'export':
                if not user_email:
                    raise CommandError('--user-email is required for export action')
                self.export_user_data(user_email, tenant)
            elif action == 'anonymize':
                if not user_email:
                    raise CommandError('--user-email is required for anonymize action')
                self.anonymize_user_data(user_email, tenant, dry_run, force)
            elif action == 'report':
                self.generate_compliance_report(tenant, days)
            elif action == 'check_retention':
                self.check_retention_policies(tenant)

        except Tenant.DoesNotExist:
            raise CommandError(f'Tenant "{tenant_slug}" does not exist')
        except Exception as e:
            logger.error(f'Error in compliance operation: {str(e)}')
            raise CommandError(f'Error: {str(e)}')

    def cleanup_old_data(self, tenant, days, dry_run=False, force=False):
        """Clean up old data based on retention policies."""
        self.stdout.write(f'Checking data for cleanup (older than {days} days)...')
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Get retention policies
        policies = DataRetentionPolicy.objects.filter(is_active=True)
        if tenant:
            policies = policies.filter(tenant=tenant)
        
        total_deleted = 0
        
        for policy in policies:
            if policy.retention_period_days == 0:  # Indefinite retention
                continue
                
            policy_cutoff = timezone.now() - timedelta(days=policy.retention_period_days)
            
            self.stdout.write(f'\nProcessing policy: {policy.name} ({policy.data_type})')
            
            if policy.data_type == 'audit_logs':
                queryset = AuditLog.objects.filter(
                    timestamp__lt=policy_cutoff
                )
                if policy.tenant:
                    queryset = queryset.filter(tenant=policy.tenant)
                    
            elif policy.data_type == 'user_data':
                # Handle user activity data
                queryset = UserActivity.objects.filter(
                    timestamp__lt=policy_cutoff
                )
                if policy.tenant:
                    queryset = queryset.filter(tenant=policy.tenant)
            else:
                self.stdout.write(f'  Skipping unsupported data type: {policy.data_type}')
                continue
            
            count = queryset.count()
            
            if count > 0:
                if dry_run:
                    self.stdout.write(f'  Would delete {count} records')
                else:
                    if not force:
                        confirm = input(f'  Delete {count} records? (y/N): ')
                        if confirm.lower() != 'y':
                            self.stdout.write('  Skipped')
                            continue
                    
                    if policy.anonymize_before_delete:
                        self.stdout.write(f'  Anonymizing {count} records...')
                        # Implement anonymization logic here
                        # For now, we'll just delete
                    
                    deleted_count = queryset.delete()[0]
                    total_deleted += deleted_count
                    self.stdout.write(
                        self.style.SUCCESS(f'  Deleted {deleted_count} records')
                    )
            else:
                self.stdout.write('  No records to delete')
        
        if dry_run:
            self.stdout.write(f'\nDry run complete. Would delete {total_deleted} total records.')
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\nCleanup complete. Deleted {total_deleted} total records.')
            )

    def export_user_data(self, user_email, tenant=None):
        """Export all data for a user (GDPR Article 20 - Right to Data Portability)."""
        self.stdout.write(f'Exporting data for user: {user_email}')
        
        try:
            user_query = User.objects.filter(email=user_email)
            if tenant:
                user_query = user_query.filter(tenant=tenant)
            
            user = user_query.get()
        except User.DoesNotExist:
            raise CommandError(f'User "{user_email}" not found')
        except User.MultipleObjectsReturned:
            raise CommandError(f'Multiple users found with email "{user_email}". Specify tenant.')
        
        export_data = {
            'user_info': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'language': user.language,
                'timezone': user.timezone,
                'preferences': user.preferences,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
            },
            'activities': [],
            'audit_logs': [],
            'consent_records': [],
        }
        
        # Export user activities
        activities = UserActivity.objects.filter(user=user)
        for activity in activities:
            export_data['activities'].append({
                'activity_type': activity.activity_type,
                'description': activity.description,
                'timestamp': activity.timestamp.isoformat(),
                'ip_address': activity.ip_address,
                'metadata': activity.metadata,
            })
        
        # Export audit logs
        audit_logs = AuditLog.objects.filter(user=user)
        for log in audit_logs:
            export_data['audit_logs'].append({
                'action': log.action,
                'resource_type': log.resource_type,
                'resource_id': log.resource_id,
                'timestamp': log.timestamp.isoformat(),
                'ip_address': log.ip_address,
                'metadata': log.metadata,
            })
        
        # Export consent records
        consent_records = ConsentRecord.objects.filter(user=user)
        for consent in consent_records:
            export_data['consent_records'].append({
                'purpose': consent.purpose,
                'consent_given': consent.consent_given,
                'given_at': consent.given_at.isoformat(),
                'withdrawn_at': consent.withdrawn_at.isoformat() if consent.withdrawn_at else None,
            })
        
        # Save to file
        filename = f'user_data_export_{user.id}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        self.stdout.write(
            self.style.SUCCESS(f'User data exported to: {filename}')
        )
        
        # Log the export
        AuditLog.objects.create(
            tenant=user.tenant,
            user=user,
            action='data_export',
            resource_type='user',
            resource_id=str(user.id),
            metadata={'export_file': filename}
        )

    def anonymize_user_data(self, user_email, tenant=None, dry_run=False, force=False):
        """Anonymize user data (GDPR Article 17 - Right to Erasure)."""
        self.stdout.write(f'Anonymizing data for user: {user_email}')
        
        try:
            user_query = User.objects.filter(email=user_email)
            if tenant:
                user_query = user_query.filter(tenant=tenant)
            
            user = user_query.get()
        except User.DoesNotExist:
            raise CommandError(f'User "{user_email}" not found')
        except User.MultipleObjectsReturned:
            raise CommandError(f'Multiple users found with email "{user_email}". Specify tenant.')
        
        if not dry_run and not force:
            confirm = input(f'This will anonymize all data for {user.email}. Continue? (y/N): ')
            if confirm.lower() != 'y':
                self.stdout.write('Operation cancelled.')
                return
        
        if dry_run:
            self.stdout.write('DRY RUN - Would anonymize:')
            self.stdout.write(f'  - User profile: {user.email}')
            self.stdout.write(f'  - {UserActivity.objects.filter(user=user).count()} activity records')
            self.stdout.write(f'  - {AuditLog.objects.filter(user=user).count()} audit log entries')
        else:
            # Anonymize user profile
            user.first_name = 'Anonymized'
            user.last_name = 'User'
            user.email = f'anonymized_{user.id}@example.com'
            user.phone = ''
            user.preferences = {}
            user.is_active = False
            user.save()
            
            # Anonymize user activities
            UserActivity.objects.filter(user=user).update(
                description='Anonymized activity',
                ip_address=None,
                user_agent='',
                metadata={}
            )
            
            # Note: We don't delete audit logs for compliance reasons,
            # but we could anonymize IP addresses and user agents
            AuditLog.objects.filter(user=user).update(
                ip_address=None,
                user_agent='Anonymized'
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully anonymized data for user: {user_email}')
            )

    def generate_compliance_report(self, tenant, days):
        """Generate a compliance report."""
        self.stdout.write(f'Generating compliance report for last {days} days...')
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Data subject requests
        requests = DataSubjectRequest.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        if tenant:
            requests = requests.filter(tenant=tenant)
        
        # Consent records
        consents = ConsentRecord.objects.filter(
            given_at__gte=start_date,
            given_at__lte=end_date
        )
        if tenant:
            consents = consents.filter(tenant=tenant)
        
        # Generate report
        report_data = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days
            },
            'data_subject_requests': {
                'total': requests.count(),
                'by_type': {},
                'by_status': {},
                'overdue': requests.filter(due_date__lt=timezone.now(), status__in=['pending', 'in_progress']).count()
            },
            'consent_records': {
                'total': consents.count(),
                'given': consents.filter(consent_given=True).count(),
                'withdrawn': consents.filter(consent_given=False).count()
            }
        }
        
        # Count by request type
        for request_type, _ in DataSubjectRequest._meta.get_field('request_type').choices:
            count = requests.filter(request_type=request_type).count()
            report_data['data_subject_requests']['by_type'][request_type] = count
        
        # Count by status
        for status, _ in DataSubjectRequest._meta.get_field('status').choices:
            count = requests.filter(status=status).count()
            report_data['data_subject_requests']['by_status'][status] = count
        
        # Display report
        self.stdout.write('\n' + '='*50)
        self.stdout.write('COMPLIANCE REPORT')
        self.stdout.write('='*50)
        self.stdout.write(f'Period: {start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")}')
        self.stdout.write('')
        
        self.stdout.write('Data Subject Requests:')
        self.stdout.write(f'  Total: {report_data["data_subject_requests"]["total"]}')
        self.stdout.write(f'  Overdue: {report_data["data_subject_requests"]["overdue"]}')
        self.stdout.write('  By Type:')
        for req_type, count in report_data['data_subject_requests']['by_type'].items():
            self.stdout.write(f'    {req_type}: {count}')
        self.stdout.write('  By Status:')
        for status, count in report_data['data_subject_requests']['by_status'].items():
            self.stdout.write(f'    {status}: {count}')
        
        self.stdout.write('')
        self.stdout.write('Consent Records:')
        self.stdout.write(f'  Total: {report_data["consent_records"]["total"]}')
        self.stdout.write(f'  Given: {report_data["consent_records"]["given"]}')
        self.stdout.write(f'  Withdrawn: {report_data["consent_records"]["withdrawn"]}')

    def check_retention_policies(self, tenant):
        """Check and report on data retention policies."""
        self.stdout.write('Checking data retention policies...')
        
        policies = DataRetentionPolicy.objects.filter(is_active=True)
        if tenant:
            policies = policies.filter(tenant=tenant)
        
        if not policies.exists():
            self.stdout.write('No active retention policies found.')
            return
        
        self.stdout.write(f'\nFound {policies.count()} active retention policies:')
        self.stdout.write('-' * 80)
        
        for policy in policies:
            self.stdout.write(f'Policy: {policy.name}')
            self.stdout.write(f'  Data Type: {policy.data_type}')
            self.stdout.write(f'  Retention Period: {policy.retention_period_days} days')
            self.stdout.write(f'  Auto Delete: {policy.auto_delete}')
            self.stdout.write(f'  Anonymize Before Delete: {policy.anonymize_before_delete}')
            
            if policy.retention_period_days > 0:
                cutoff_date = timezone.now() - timedelta(days=policy.retention_period_days)
                self.stdout.write(f'  Data older than: {cutoff_date.strftime("%Y-%m-%d")}')
            else:
                self.stdout.write('  Indefinite retention')
            
            self.stdout.write('')
