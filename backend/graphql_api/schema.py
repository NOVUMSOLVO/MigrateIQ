"""
GraphQL schema for MigrateIQ API.
"""

import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
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


class TenantType(DjangoObjectType):
    class Meta:
        model = Tenant
        fields = ('id', 'name', 'slug', 'is_active', 'created_at', 'updated_at')


class AuditLogType(DjangoObjectType):
    class Meta:
        model = AuditLog
        fields = ('id', 'action', 'object_type', 'object_id', 'user', 'tenant', 'timestamp', 'ip_address')


class SystemConfigurationType(DjangoObjectType):
    class Meta:
        model = SystemConfiguration
        fields = ('id', 'key', 'value', 'description', 'is_active')


class MigrationProjectType(DjangoObjectType):
    class Meta:
        model = MigrationProject
        fields = ('id', 'name', 'description', 'status', 'created_at', 'updated_at', 'tenant')


class MigrationTaskType(DjangoObjectType):
    class Meta:
        model = MigrationTask
        fields = ('id', 'name', 'status', 'project', 'created_at', 'updated_at')


class DataSourceType(DjangoObjectType):
    class Meta:
        model = DataSource
        fields = ('id', 'name', 'type', 'connection_string', 'is_active', 'tenant')


class EntityType(DjangoObjectType):
    class Meta:
        model = Entity
        fields = ('id', 'name', 'type', 'data_source', 'schema_info')


class ValidationRuleType(DjangoObjectType):
    class Meta:
        model = ValidationRule
        fields = ('id', 'name', 'rule_type', 'configuration', 'is_active')


class ValidationJobType(DjangoObjectType):
    class Meta:
        model = ValidationJob
        fields = ('id', 'name', 'status', 'created_at', 'completed_at')


# Query class
class Query(graphene.ObjectType):
    # User queries
    me = graphene.Field(UserType)
    users = DjangoFilterConnectionField(UserType)
    
    # Tenant queries
    current_tenant = graphene.Field(TenantType)
    tenants = DjangoFilterConnectionField(TenantType)
    
    # Audit log queries
    audit_logs = DjangoFilterConnectionField(AuditLogType)
    
    # System configuration queries
    system_configurations = DjangoFilterConnectionField(SystemConfigurationType)
    system_config = graphene.Field(SystemConfigurationType, key=graphene.String(required=True))
    
    # Migration project queries
    migration_projects = DjangoFilterConnectionField(MigrationProjectType)
    migration_project = graphene.Field(MigrationProjectType, id=graphene.ID(required=True))
    
    # Migration task queries
    migration_tasks = DjangoFilterConnectionField(MigrationTaskType)
    migration_task = graphene.Field(MigrationTaskType, id=graphene.ID(required=True))
    
    # Data source queries
    data_sources = DjangoFilterConnectionField(DataSourceType)
    data_source = graphene.Field(DataSourceType, id=graphene.ID(required=True))
    
    # Entity queries
    entities = DjangoFilterConnectionField(EntityType)
    entity = graphene.Field(EntityType, id=graphene.ID(required=True))
    
    # Validation queries
    validation_rules = DjangoFilterConnectionField(ValidationRuleType)
    validation_jobs = DjangoFilterConnectionField(ValidationJobType)

    @login_required
    def resolve_me(self, info):
        """Get current user."""
        return info.context.user

    @login_required
    def resolve_current_tenant(self, info):
        """Get current user's tenant."""
        return getattr(info.context.user, 'tenant', None)

    @login_required
    def resolve_system_config(self, info, key):
        """Get system configuration by key."""
        try:
            return SystemConfiguration.objects.get(key=key, is_active=True)
        except SystemConfiguration.DoesNotExist:
            return None

    @login_required
    def resolve_migration_project(self, info, id):
        """Get migration project by ID."""
        try:
            return MigrationProject.objects.get(id=id, tenant=info.context.user.tenant)
        except MigrationProject.DoesNotExist:
            return None

    @login_required
    def resolve_migration_task(self, info, id):
        """Get migration task by ID."""
        try:
            return MigrationTask.objects.get(id=id, project__tenant=info.context.user.tenant)
        except MigrationTask.DoesNotExist:
            return None

    @login_required
    def resolve_data_source(self, info, id):
        """Get data source by ID."""
        try:
            return DataSource.objects.get(id=id, tenant=info.context.user.tenant)
        except DataSource.DoesNotExist:
            return None

    @login_required
    def resolve_entity(self, info, id):
        """Get entity by ID."""
        try:
            return Entity.objects.get(id=id, data_source__tenant=info.context.user.tenant)
        except Entity.DoesNotExist:
            return None


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
                tenant=info.context.user.tenant
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
            project = MigrationProject.objects.get(id=id, tenant=info.context.user.tenant)
            
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
            project = MigrationProject.objects.get(id=id, tenant=info.context.user.tenant)
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
                type=type,
                connection_string=connection_string,
                tenant=info.context.user.tenant
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
