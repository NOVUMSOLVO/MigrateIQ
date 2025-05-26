"""
Comprehensive tests for API endpoints.
"""

import json
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch, MagicMock

from core.models import Tenant
from analyzer.models import DataSource, Entity, Field
from orchestrator.models import MigrationProject, MigrationTask

User = get_user_model()


class AuthenticationAPITests(APITestCase):
    """Test authentication API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Update user with tenant
        self.user.tenant = self.tenant
        self.user.save()

    def test_user_registration(self):
        """Test user registration endpoint."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'tenant_slug': self.tenant.slug
        }

        response = self.client.post('/api/auth/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_user_login(self):
        """Test user login endpoint."""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }

        response = self.client.post('/api/auth/login/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_token_refresh(self):
        """Test token refresh endpoint."""
        refresh = RefreshToken.for_user(self.user)
        data = {'refresh': str(refresh)}

        response = self.client.post('/api/auth/token/refresh/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_user_profile_endpoint(self):
        """Test user profile endpoint."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get('/api/auth/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')


class DataSourceAPITests(APITestCase):
    """Test data source API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Update user with tenant
        self.user.tenant = self.tenant
        self.user.save()
        self.client.force_authenticate(user=self.user)

        self.data_source = DataSource.objects.create(
            name='Test Database',
            source_type='postgresql',
            connection_string='postgresql://user:pass@localhost:5432/db'
        )

    def test_list_data_sources(self):
        """Test listing data sources."""
        response = self.client.get('/api/analyzer/data-sources/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Database')

    def test_create_data_source(self):
        """Test creating a data source."""
        data = {
            'name': 'New Database',
            'source_type': 'mysql',
            'connection_string': 'mysql://user:pass@localhost:3306/db'
        }

        response = self.client.post('/api/analyzer/data-sources/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Database')
        self.assertTrue(DataSource.objects.filter(name='New Database').exists())

    def test_retrieve_data_source(self):
        """Test retrieving a specific data source."""
        response = self.client.get(f'/api/analyzer/data-sources/{self.data_source.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Database')

    def test_update_data_source(self):
        """Test updating a data source."""
        data = {
            'name': 'Updated Database',
            'source_type': 'postgresql',
            'connection_string': 'postgresql://user:pass@localhost:5432/updated_db'
        }

        response = self.client.put(f'/api/analyzer/data-sources/{self.data_source.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Database')

        self.data_source.refresh_from_db()
        self.assertEqual(self.data_source.name, 'Updated Database')

    def test_delete_data_source(self):
        """Test deleting a data source."""
        response = self.client.delete(f'/api/analyzer/data-sources/{self.data_source.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(DataSource.objects.filter(id=self.data_source.id).exists())


class EntityAPITests(APITestCase):
    """Test entity API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Update user with tenant
        self.user.tenant = self.tenant
        self.user.save()
        self.client.force_authenticate(user=self.user)

        self.data_source = DataSource.objects.create(
            name='Test Database',
            source_type='postgresql'
        )
        self.entity = Entity.objects.create(
            data_source=self.data_source,
            name='customers',
            original_name='customers',
            record_count=1000
        )

    def test_list_entities(self):
        """Test listing entities."""
        response = self.client.get('/api/analyzer/entities/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'customers')

    def test_create_entity(self):
        """Test creating an entity."""
        data = {
            'data_source': self.data_source.id,
            'name': 'orders',
            'original_name': 'orders',
            'record_count': 500,
            'description': 'Order data table'
        }

        response = self.client.post('/api/analyzer/entities/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'orders')
        self.assertTrue(Entity.objects.filter(name='orders').exists())

    def test_filter_entities_by_data_source(self):
        """Test filtering entities by data source."""
        # Create another data source and entity
        other_data_source = DataSource.objects.create(
            name='Other Database',
            source_type='mysql'
        )
        Entity.objects.create(
            data_source=other_data_source,
            name='products',
            original_name='products'
        )

        response = self.client.get(f'/api/analyzer/entities/?data_source={self.data_source.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'customers')


class MigrationProjectAPITests(APITestCase):
    """Test migration project API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Update user with tenant
        self.user.tenant = self.tenant
        self.user.save()
        self.client.force_authenticate(user=self.user)

        self.project = MigrationProject.objects.create(
            name='Customer Migration',
            description='Migrate customer data',
            source_system='Legacy CRM',
            target_system='New CRM',
            status='DRAFT'
        )

    def test_list_migration_projects(self):
        """Test listing migration projects."""
        response = self.client.get('/api/orchestrator/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Customer Migration')

    def test_create_migration_project(self):
        """Test creating a migration project."""
        data = {
            'name': 'Product Migration',
            'description': 'Migrate product data',
            'source_system': 'Old Inventory',
            'target_system': 'New Inventory',
            'status': 'DRAFT'
        }

        response = self.client.post('/api/orchestrator/projects/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Product Migration')
        self.assertTrue(MigrationProject.objects.filter(name='Product Migration').exists())

    def test_update_project_status(self):
        """Test updating project status."""
        data = {
            'name': 'Customer Migration',
            'description': 'Migrate customer data',
            'source_system': 'Legacy CRM',
            'target_system': 'New CRM',
            'status': 'IN_PROGRESS'
        }

        response = self.client.put(f'/api/orchestrator/projects/{self.project.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'IN_PROGRESS')

        self.project.refresh_from_db()
        self.assertEqual(self.project.status, 'IN_PROGRESS')


class APIPermissionTests(APITestCase):
    """Test API permission and authorization."""

    def setUp(self):
        """Set up test data."""
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Update user with tenant
        self.user.tenant = self.tenant
        self.user.save()

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are denied."""
        response = self.client.get('/api/analyzer/data-sources/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_access_allowed(self):
        """Test that authenticated requests are allowed."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/analyzer/data-sources/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class APIValidationTests(APITestCase):
    """Test API input validation."""

    def setUp(self):
        """Set up test data."""
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Update user with tenant
        self.user.tenant = self.tenant
        self.user.save()
        self.client.force_authenticate(user=self.user)

    def test_create_data_source_missing_required_fields(self):
        """Test creating data source with missing required fields."""
        data = {
            'source_type': 'postgresql'
            # Missing 'name' field
        }

        response = self.client.post('/api/analyzer/data-sources/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)

    def test_create_data_source_invalid_data_types(self):
        """Test creating data source with invalid data types."""
        data = {
            'name': 123,  # Should be string
            'source_type': 'postgresql'
        }

        response = self.client.post('/api/analyzer/data-sources/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_migration_project_invalid_status(self):
        """Test creating migration project with invalid status."""
        data = {
            'name': 'Test Project',
            'source_system': 'Source',
            'target_system': 'Target',
            'status': 'INVALID_STATUS'
        }

        response = self.client.post('/api/orchestrator/projects/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('status', response.data)


@pytest.mark.django_db
class APIPerformanceTests:
    """Test API performance with pytest."""

    def test_data_source_list_pagination(self):
        """Test data source list pagination performance."""
        # Create multiple data sources
        for i in range(50):
            DataSource.objects.create(
                name=f'Database {i}',
                source_type='postgresql'
            )

        client = APIClient()
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client.force_authenticate(user=user)

        # Test pagination
        response = client.get('/api/analyzer/data-sources/?page=1&page_size=10')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 10
        assert 'next' in response.data
        assert 'previous' in response.data

    def test_entity_list_with_fields(self):
        """Test entity list with nested fields performance."""
        data_source = DataSource.objects.create(
            name='Test DB',
            source_type='postgresql'
        )

        # Create entity with many fields
        entity = Entity.objects.create(
            data_source=data_source,
            name='large_table',
            original_name='large_table'
        )

        for i in range(100):
            Field.objects.create(
                entity=entity,
                name=f'field_{i}',
                original_name=f'field_{i}',
                data_type='string'
            )

        client = APIClient()
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        client.force_authenticate(user=user)

        import time
        start_time = time.time()
        response = client.get(f'/api/analyzer/entities/{entity.id}/')
        end_time = time.time()

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['fields']) == 100
        assert end_time - start_time < 2.0  # Should complete within 2 seconds
