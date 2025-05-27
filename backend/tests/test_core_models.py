"""
Comprehensive tests for core models and functionality.
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from unittest.mock import patch, MagicMock

from core.models import Tenant, SystemConfiguration
from analyzer.models import DataSource, Entity, Field
from orchestrator.models import MigrationProject, MigrationTask
from mapping_engine.models import Mapping, FieldMapping

User = get_user_model()


class TenantModelTests(TestCase):
    """Test the Tenant model."""

    def test_create_tenant(self):
        """Test creating a tenant."""
        tenant = Tenant.objects.create(
            name='Test Company',
            slug='test-company',
            plan='basic',
            is_active=True
        )

        self.assertEqual(tenant.name, 'Test Company')
        self.assertEqual(tenant.slug, 'test-company')
        self.assertEqual(tenant.plan, 'basic')
        self.assertTrue(tenant.is_active)
        self.assertIsNotNone(tenant.created_at)

    def test_tenant_slug_uniqueness(self):
        """Test that tenant slugs must be unique."""
        Tenant.objects.create(name='Company 1', slug='test-slug')

        with self.assertRaises(IntegrityError):
            Tenant.objects.create(name='Company 2', slug='test-slug')

    def test_tenant_str_representation(self):
        """Test tenant string representation."""
        tenant = Tenant.objects.create(name='Test Company', slug='test-company')
        self.assertEqual(str(tenant), 'Test Company')

    def test_tenant_subscription_tiers(self):
        """Test valid subscription tiers."""
        valid_tiers = ['free', 'basic', 'professional', 'enterprise']

        for tier in valid_tiers:
            tenant = Tenant.objects.create(
                name=f'Company {tier}',
                slug=f'company-{tier}',
                plan=tier
            )
            self.assertEqual(tenant.plan, tier)


class UserModelTests(TestCase):
    """Test the User model."""

    def setUp(self):
        """Set up test data."""
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant'
        )

    def test_create_user_with_tenant(self):
        """Test creating a user with additional fields."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role='admin',
            phone='+1234567890'
        )

        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.role, 'admin')
        self.assertEqual(user.phone, '+1234567890')

    def test_user_str_representation(self):
        """Test user string representation."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        expected = 'Test User (test@example.com)'
        self.assertEqual(str(user), expected)


class DataSourceModelTests(TestCase):
    """Test the DataSource model."""

    def test_create_data_source(self):
        """Test creating a data source."""
        data_source = DataSource.objects.create(
            name='Test Database',
            source_type='postgresql',
            connection_string='postgresql://user:pass@localhost:5432/db'
        )

        self.assertEqual(data_source.name, 'Test Database')
        self.assertEqual(data_source.source_type, 'postgresql')
        self.assertIsNotNone(data_source.created_at)
        self.assertIsNotNone(data_source.updated_at)

    def test_data_source_str_representation(self):
        """Test data source string representation."""
        data_source = DataSource.objects.create(
            name='Test Database',
            source_type='postgresql'
        )
        self.assertEqual(str(data_source), 'Test Database')


class EntityModelTests(TestCase):
    """Test the Entity model."""

    def setUp(self):
        """Set up test data."""
        self.data_source = DataSource.objects.create(
            name='Test Database',
            source_type='postgresql'
        )

    def test_create_entity(self):
        """Test creating an entity."""
        entity = Entity.objects.create(
            data_source=self.data_source,
            name='customers',
            original_name='customers',
            record_count=1000,
            description='Customer data table'
        )

        self.assertEqual(entity.data_source, self.data_source)
        self.assertEqual(entity.name, 'customers')
        self.assertEqual(entity.original_name, 'customers')
        self.assertEqual(entity.record_count, 1000)
        self.assertEqual(entity.description, 'Customer data table')

    def test_entity_str_representation(self):
        """Test entity string representation."""
        entity = Entity.objects.create(
            data_source=self.data_source,
            name='customers',
            original_name='customers'
        )
        expected = f'{self.data_source.name} - customers'
        self.assertEqual(str(entity), expected)


class FieldModelTests(TestCase):
    """Test the Field model."""

    def setUp(self):
        """Set up test data."""
        self.data_source = DataSource.objects.create(
            name='Test Database',
            source_type='postgresql'
        )
        self.entity = Entity.objects.create(
            data_source=self.data_source,
            name='customers',
            original_name='customers'
        )

    def test_create_field(self):
        """Test creating a field."""
        field = Field.objects.create(
            entity=self.entity,
            name='customer_id',
            original_name='customer_id',
            data_type='integer',
            is_primary_key=True,
            is_nullable=False,
            sample_values=[1, 2, 3, 4, 5]
        )

        self.assertEqual(field.entity, self.entity)
        self.assertEqual(field.name, 'customer_id')
        self.assertEqual(field.data_type, 'integer')
        self.assertTrue(field.is_primary_key)
        self.assertFalse(field.is_nullable)
        self.assertEqual(field.sample_values, [1, 2, 3, 4, 5])

    def test_field_str_representation(self):
        """Test field string representation."""
        field = Field.objects.create(
            entity=self.entity,
            name='customer_id',
            original_name='customer_id',
            data_type='integer'
        )
        expected = f'{self.entity.name} - customer_id'
        self.assertEqual(str(field), expected)


class MigrationProjectModelTests(TestCase):
    """Test the MigrationProject model."""

    def test_create_migration_project(self):
        """Test creating a migration project."""
        project = MigrationProject.objects.create(
            name='Customer Migration',
            description='Migrate customer data from legacy system',
            source_system='Legacy CRM',
            target_system='New CRM',
            status='DRAFT'
        )

        self.assertEqual(project.name, 'Customer Migration')
        self.assertEqual(project.source_system, 'Legacy CRM')
        self.assertEqual(project.target_system, 'New CRM')
        self.assertEqual(project.status, 'DRAFT')
        self.assertIsNotNone(project.created_at)

    def test_migration_project_str_representation(self):
        """Test migration project string representation."""
        project = MigrationProject.objects.create(
            name='Customer Migration',
            source_system='Legacy CRM',
            target_system='New CRM'
        )
        self.assertEqual(str(project), 'Customer Migration')


class MigrationTaskModelTests(TestCase):
    """Test the MigrationTask model."""

    def setUp(self):
        """Set up test data."""
        self.project = MigrationProject.objects.create(
            name='Customer Migration',
            source_system='Legacy CRM',
            target_system='New CRM'
        )

    def test_create_migration_task(self):
        """Test creating a migration task."""
        task = MigrationTask.objects.create(
            project=self.project,
            name='Analyze Customer Data',
            task_type='ANALYSIS',
            status='PENDING'
        )

        self.assertEqual(task.project, self.project)
        self.assertEqual(task.name, 'Analyze Customer Data')
        self.assertEqual(task.task_type, 'ANALYSIS')
        self.assertEqual(task.status, 'PENDING')

    def test_migration_task_str_representation(self):
        """Test migration task string representation."""
        task = MigrationTask.objects.create(
            project=self.project,
            name='Analyze Customer Data',
            task_type='ANALYSIS'
        )
        expected = f'{self.project.name} - Analyze Customer Data'
        self.assertEqual(str(task), expected)


@pytest.mark.django_db
class ModelRelationshipTests:
    """Test model relationships using pytest."""

    def test_data_source_entity_relationship(self):
        """Test DataSource to Entity relationship."""
        data_source = DataSource.objects.create(
            name='Test DB',
            source_type='postgresql'
        )

        entity1 = Entity.objects.create(
            data_source=data_source,
            name='customers',
            original_name='customers'
        )
        entity2 = Entity.objects.create(
            data_source=data_source,
            name='orders',
            original_name='orders'
        )

        assert data_source.entities.count() == 2
        assert entity1 in data_source.entities.all()
        assert entity2 in data_source.entities.all()

    def test_entity_field_relationship(self):
        """Test Entity to Field relationship."""
        data_source = DataSource.objects.create(
            name='Test DB',
            source_type='postgresql'
        )
        entity = Entity.objects.create(
            data_source=data_source,
            name='customers',
            original_name='customers'
        )

        field1 = Field.objects.create(
            entity=entity,
            name='id',
            original_name='id',
            data_type='integer'
        )
        field2 = Field.objects.create(
            entity=entity,
            name='name',
            original_name='name',
            data_type='string'
        )

        assert entity.fields.count() == 2
        assert field1 in entity.fields.all()
        assert field2 in entity.fields.all()

    def test_project_task_relationship(self):
        """Test MigrationProject to MigrationTask relationship."""
        project = MigrationProject.objects.create(
            name='Test Project',
            source_system='Source',
            target_system='Target'
        )

        task1 = MigrationTask.objects.create(
            project=project,
            name='Task 1',
            task_type='ANALYSIS'
        )
        task2 = MigrationTask.objects.create(
            project=project,
            name='Task 2',
            task_type='MAPPING'
        )

        assert project.tasks.count() == 2
        assert task1 in project.tasks.all()
        assert task2 in project.tasks.all()
