"""
GraphQL schema for MigrateIQ API.
"""

import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphene import relay
from graphql_jwt.decorators import login_required
from django.contrib.auth import get_user_model
from core.models import Tenant, AuditLog, SystemConfiguration
from orchestrator.models import MigrationProject, MigrationTask
from analyzer.models import DataSource, Entity
from validation.models import ValidationRule, ValidationJob

User = get_user_model()


# Object Types
class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined')
        interfaces = (relay.Node,)


class TenantType(DjangoObjectType):
    class Meta:
        model = Tenant
        fields = ('id', 'name', 'slug', 'is_active', 'created_at', 'updated_at')
        interfaces = (relay.Node,)


class AuditLogType(DjangoObjectType):
    class Meta:
        model = AuditLog
        fields = ('id', 'action', 'resource_type', 'resource_id', 'user', 'tenant', 'timestamp', 'ip_address')
        interfaces = (relay.Node,)


class SystemConfigurationType(DjangoObjectType):
    class Meta:
        model = SystemConfiguration
        fields = ('id', 'key', 'value', 'description', 'is_active')
        interfaces = (relay.Node,)


class MigrationProjectType(DjangoObjectType):
    class Meta:
        model = MigrationProject
        fields = ('id', 'name', 'description', 'status', 'created_at', 'updated_at')
        interfaces = (relay.Node,)


class MigrationTaskType(DjangoObjectType):
    class Meta:
        model = MigrationTask
        fields = ('id', 'name', 'status', 'project', 'created_at', 'updated_at')
        interfaces = (relay.Node,)


class DataSourceType(DjangoObjectType):
    class Meta:
        model = DataSource
        fields = ('id', 'name', 'source_type', 'connection_string')
        interfaces = (relay.Node,)


class EntityType(DjangoObjectType):
    class Meta:
        model = Entity
        fields = ('id', 'name', 'description', 'data_source', 'record_count')
        interfaces = (relay.Node,)


class ValidationRuleType(DjangoObjectType):
    class Meta:
        model = ValidationRule
        fields = ('id', 'name', 'rule_type', 'rule_definition', 'is_critical')
        interfaces = (relay.Node,)


class ValidationJobType(DjangoObjectType):
    class Meta:
        model = ValidationJob
        fields = ('id', 'status', 'started_at', 'completed_at', 'records_processed')
        interfaces = (relay.Node,)


# Query class
class Query(graphene.ObjectType):
    # User queries
    me = graphene.Field(UserType)
    users = graphene.List(UserType)

    # Tenant queries
    current_tenant = graphene.Field(TenantType)
    tenants = graphene.List(TenantType)

    # Audit log queries
    audit_logs = graphene.List(AuditLogType)

    # System configuration queries
    system_configurations = graphene.List(SystemConfigurationType)
    system_config = graphene.Field(SystemConfigurationType, key=graphene.String(required=True))

    # Migration project queries
    migration_projects = graphene.List(MigrationProjectType)
    migration_project = graphene.Field(MigrationProjectType, id=graphene.ID(required=True))

    # Migration task queries
    migration_tasks = graphene.List(MigrationTaskType)
    migration_task = graphene.Field(MigrationTaskType, id=graphene.ID(required=True))

    # Data source queries
    data_sources = graphene.List(DataSourceType)
    data_source = graphene.Field(DataSourceType, id=graphene.ID(required=True))

    # Entity queries
    entities = graphene.List(EntityType)
    entity = graphene.Field(EntityType, id=graphene.ID(required=True))

    # Validation queries
    validation_rules = graphene.List(ValidationRuleType)
    validation_jobs = graphene.List(ValidationJobType)

    @login_required
    def resolve_me(self, info):
        """Get current user."""
        return info.context.user

    @login_required
    def resolve_users(self, info):
        """Get all users."""
        return User.objects.all()

    @login_required
    def resolve_current_tenant(self, info):
        """Get current user's tenant."""
        return getattr(info.context.user, 'tenant', None)

    @login_required
    def resolve_tenants(self, info):
        """Get all tenants."""
        return Tenant.objects.all()

    @login_required
    def resolve_audit_logs(self, info):
        """Get audit logs."""
        return AuditLog.objects.all()

    @login_required
    def resolve_system_configurations(self, info):
        """Get system configurations."""
        return SystemConfiguration.objects.filter(is_active=True)

    @login_required
    def resolve_system_config(self, info, key):
        """Get system configuration by key."""
        try:
            return SystemConfiguration.objects.get(key=key, is_active=True)
        except SystemConfiguration.DoesNotExist:
            return None

    @login_required
    def resolve_migration_projects(self, info):
        """Get migration projects."""
        return MigrationProject.objects.all()

    @login_required
    def resolve_migration_project(self, info, id):
        """Get migration project by ID."""
        try:
            return MigrationProject.objects.get(id=id)
        except MigrationProject.DoesNotExist:
            return None

    @login_required
    def resolve_migration_tasks(self, info):
        """Get migration tasks."""
        return MigrationTask.objects.all()

    @login_required
    def resolve_migration_task(self, info, id):
        """Get migration task by ID."""
        try:
            return MigrationTask.objects.get(id=id)
        except MigrationTask.DoesNotExist:
            return None

    @login_required
    def resolve_data_sources(self, info):
        """Get data sources."""
        return DataSource.objects.all()

    @login_required
    def resolve_data_source(self, info, id):
        """Get data source by ID."""
        try:
            return DataSource.objects.get(id=id)
        except DataSource.DoesNotExist:
            return None

    @login_required
    def resolve_entities(self, info):
        """Get entities."""
        return Entity.objects.all()

    @login_required
    def resolve_entity(self, info, id):
        """Get entity by ID."""
        try:
            return Entity.objects.get(id=id)
        except Entity.DoesNotExist:
            return None

    @login_required
    def resolve_validation_rules(self, info):
        """Get validation rules."""
        return ValidationRule.objects.all()

    @login_required
    def resolve_validation_jobs(self, info):
        """Get validation jobs."""
        return ValidationJob.objects.all()


# Mutation classes
class CreateMigrationProject(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String()

    migration_project = graphene.Field(MigrationProjectType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @login_required
    def mutate(self, info, name, description=None):
        try:
            project = MigrationProject.objects.create(
                name=name,
                description=description or '',
                source_system='Source',
                target_system='Target'
            )
            return CreateMigrationProject(
                migration_project=project,
                success=True,
                errors=[]
            )
        except Exception as e:
            return CreateMigrationProject(
                migration_project=None,
                success=False,
                errors=[str(e)]
            )


class UpdateMigrationProject(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String()
        description = graphene.String()

    migration_project = graphene.Field(MigrationProjectType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @login_required
    def mutate(self, info, id, name=None, description=None):
        try:
            project = MigrationProject.objects.get(id=id)

            if name is not None:
                project.name = name
            if description is not None:
                project.description = description

            project.save()

            return UpdateMigrationProject(
                migration_project=project,
                success=True,
                errors=[]
            )
        except MigrationProject.DoesNotExist:
            return UpdateMigrationProject(
                migration_project=None,
                success=False,
                errors=['Migration project not found']
            )
        except Exception as e:
            return UpdateMigrationProject(
                migration_project=None,
                success=False,
                errors=[str(e)]
            )


class DeleteMigrationProject(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @login_required
    def mutate(self, info, id):
        try:
            project = MigrationProject.objects.get(id=id)
            project.delete()

            return DeleteMigrationProject(
                success=True,
                errors=[]
            )
        except MigrationProject.DoesNotExist:
            return DeleteMigrationProject(
                success=False,
                errors=['Migration project not found']
            )
        except Exception as e:
            return DeleteMigrationProject(
                success=False,
                errors=[str(e)]
            )


class CreateDataSource(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        type = graphene.String(required=True)
        connection_string = graphene.String(required=True)

    data_source = graphene.Field(DataSourceType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @login_required
    def mutate(self, info, name, type, connection_string):
        try:
            data_source = DataSource.objects.create(
                name=name,
                source_type=type,
                connection_string=connection_string
            )
            return CreateDataSource(
                data_source=data_source,
                success=True,
                errors=[]
            )
        except Exception as e:
            return CreateDataSource(
                data_source=None,
                success=False,
                errors=[str(e)]
            )


# Root Mutation class
class Mutation(graphene.ObjectType):
    create_migration_project = CreateMigrationProject.Field()
    update_migration_project = UpdateMigrationProject.Field()
    delete_migration_project = DeleteMigrationProject.Field()
    create_data_source = CreateDataSource.Field()


# Schema
schema = graphene.Schema(query=Query, mutation=Mutation)
