# Generated by Django 4.2.7 on 2025-05-26 23:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('key', models.CharField(max_length=100, unique=True, verbose_name='Key')),
                ('value', models.JSONField(verbose_name='Value')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('is_sensitive', models.BooleanField(default=False, verbose_name='Is sensitive')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is active')),
            ],
            options={
                'verbose_name': 'System configuration',
                'verbose_name_plural': 'System configurations',
                'ordering': ['key'],
            },
        ),
        migrations.CreateModel(
            name='Tenant',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('slug', models.SlugField(unique=True, verbose_name='Slug')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is active')),
                ('plan', models.CharField(choices=[('free', 'Free'), ('basic', 'Basic'), ('professional', 'Professional'), ('enterprise', 'Enterprise')], default='free', max_length=20, verbose_name='Plan')),
                ('max_users', models.PositiveIntegerField(default=5, verbose_name='Max users')),
                ('max_projects', models.PositiveIntegerField(default=10, verbose_name='Max projects')),
                ('max_data_sources', models.PositiveIntegerField(default=20, verbose_name='Max data sources')),
                ('max_storage_gb', models.PositiveIntegerField(default=10, verbose_name='Max storage (GB)')),
                ('max_api_calls_per_hour', models.PositiveIntegerField(default=1000, verbose_name='Max API calls per hour')),
                ('sso_enabled', models.BooleanField(default=False, verbose_name='SSO Enabled')),
                ('sso_provider', models.CharField(blank=True, choices=[('saml', 'SAML'), ('oauth2', 'OAuth2'), ('ldap', 'LDAP')], max_length=50, verbose_name='SSO Provider')),
                ('sso_config', models.JSONField(blank=True, default=dict, verbose_name='SSO Configuration')),
                ('gdpr_enabled', models.BooleanField(default=True, verbose_name='GDPR Enabled')),
                ('data_retention_days', models.PositiveIntegerField(default=2555, verbose_name='Data Retention Days')),
                ('audit_log_retention_days', models.PositiveIntegerField(default=2555, verbose_name='Audit Log Retention Days')),
                ('logo_url', models.URLField(blank=True, verbose_name='Logo URL')),
                ('primary_color', models.CharField(blank=True, max_length=7, verbose_name='Primary Color')),
                ('secondary_color', models.CharField(blank=True, max_length=7, verbose_name='Secondary Color')),
                ('settings', models.JSONField(blank=True, default=dict, verbose_name='Settings')),
            ],
            options={
                'verbose_name': 'Tenant',
                'verbose_name_plural': 'Tenants',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='TenantQuota',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('current_users', models.PositiveIntegerField(default=0, verbose_name='Current Users')),
                ('current_projects', models.PositiveIntegerField(default=0, verbose_name='Current Projects')),
                ('current_data_sources', models.PositiveIntegerField(default=0, verbose_name='Current Data Sources')),
                ('current_storage_gb', models.FloatField(default=0.0, verbose_name='Current Storage (GB)')),
                ('api_calls_today', models.PositiveIntegerField(default=0, verbose_name='API Calls Today')),
                ('api_calls_this_hour', models.PositiveIntegerField(default=0, verbose_name='API Calls This Hour')),
                ('last_api_call_reset', models.DateTimeField(auto_now_add=True, verbose_name='Last API Call Reset')),
                ('user_warning_threshold', models.FloatField(default=0.8, verbose_name='User Warning Threshold')),
                ('storage_warning_threshold', models.FloatField(default=0.8, verbose_name='Storage Warning Threshold')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('tenant', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='quota', to='core.tenant', verbose_name='Tenant')),
            ],
            options={
                'verbose_name': 'Tenant Quota',
                'verbose_name_plural': 'Tenant Quotas',
            },
        ),
        migrations.CreateModel(
            name='Feature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Name')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('is_enabled', models.BooleanField(default=False, verbose_name='Is enabled')),
                ('rollout_percentage', models.PositiveSmallIntegerField(default=0, help_text='Percentage of users who should see this feature', verbose_name='Rollout percentage')),
                ('tenant_whitelist', models.ManyToManyField(blank=True, related_name='whitelisted_features', to='core.tenant', verbose_name='Tenant whitelist')),
            ],
            options={
                'verbose_name': 'Feature',
                'verbose_name_plural': 'Features',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='TenantUsage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('user_count', models.PositiveIntegerField(default=0, verbose_name='User Count')),
                ('project_count', models.PositiveIntegerField(default=0, verbose_name='Project Count')),
                ('data_source_count', models.PositiveIntegerField(default=0, verbose_name='Data Source Count')),
                ('storage_used_gb', models.FloatField(default=0.0, verbose_name='Storage Used (GB)')),
                ('api_calls_count', models.PositiveIntegerField(default=0, verbose_name='API Calls Count')),
                ('billing_period_start', models.DateTimeField(verbose_name='Billing Period Start')),
                ('billing_period_end', models.DateTimeField(verbose_name='Billing Period End')),
                ('base_cost', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Base Cost')),
                ('overage_cost', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Overage Cost')),
                ('total_cost', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Total Cost')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usage_records', to='core.tenant', verbose_name='Tenant')),
            ],
            options={
                'verbose_name': 'Tenant Usage',
                'verbose_name_plural': 'Tenant Usage Records',
                'ordering': ['-billing_period_start'],
                'unique_together': {('tenant', 'billing_period_start')},
            },
        ),
        migrations.CreateModel(
            name='TenantNotification',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200, verbose_name='Title')),
                ('message', models.TextField(verbose_name='Message')),
                ('notification_type', models.CharField(choices=[('info', 'Information'), ('warning', 'Warning'), ('error', 'Error'), ('quota_warning', 'Quota Warning'), ('quota_exceeded', 'Quota Exceeded'), ('maintenance', 'Maintenance'), ('feature_update', 'Feature Update')], max_length=30, verbose_name='Type')),
                ('target_roles', models.JSONField(blank=True, default=list, help_text='List of roles to target (empty means all users)', verbose_name='Target Roles')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is Active')),
                ('is_dismissible', models.BooleanField(default=True, verbose_name='Is Dismissible')),
                ('show_from', models.DateTimeField(blank=True, null=True, verbose_name='Show From')),
                ('show_until', models.DateTimeField(blank=True, null=True, verbose_name='Show Until')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('target_users', models.ManyToManyField(blank=True, related_name='tenant_notifications', to=settings.AUTH_USER_MODEL, verbose_name='Target Users')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='core.tenant', verbose_name='Tenant')),
            ],
            options={
                'verbose_name': 'Tenant Notification',
                'verbose_name_plural': 'Tenant Notifications',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['tenant', 'is_active'], name='core_tenant_tenant__400a47_idx'), models.Index(fields=['show_from', 'show_until'], name='core_tenant_show_fr_32d8df_idx')],
            },
        ),
        migrations.CreateModel(
            name='Domain',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('domain', models.CharField(max_length=253, unique=True, verbose_name='Domain')),
                ('is_primary', models.BooleanField(default=False, verbose_name='Is primary')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is active')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='domains', to='core.tenant', verbose_name='Tenant')),
            ],
            options={
                'verbose_name': 'Domain',
                'verbose_name_plural': 'Domains',
                'unique_together': {('tenant', 'is_primary')},
            },
        ),
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('action', models.CharField(max_length=100, verbose_name='Action')),
                ('resource_type', models.CharField(max_length=100, verbose_name='Resource type')),
                ('resource_id', models.CharField(blank=True, max_length=100, null=True, verbose_name='Resource ID')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP address')),
                ('user_agent', models.TextField(blank=True, verbose_name='User agent')),
                ('changes', models.JSONField(blank=True, default=dict, verbose_name='Changes')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='Metadata')),
                ('timestamp', models.DateTimeField(auto_now_add=True, verbose_name='Timestamp')),
                ('tenant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='audit_logs', to='core.tenant', verbose_name='Tenant')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Audit log',
                'verbose_name_plural': 'Audit logs',
                'ordering': ['-timestamp'],
                'indexes': [models.Index(fields=['tenant', 'timestamp'], name='core_auditl_tenant__4440e3_idx'), models.Index(fields=['user', 'timestamp'], name='core_auditl_user_id_7b678c_idx'), models.Index(fields=['action', 'timestamp'], name='core_auditl_action_096de0_idx'), models.Index(fields=['resource_type', 'resource_id'], name='core_auditl_resourc_a674ad_idx')],
            },
        ),
    ]
