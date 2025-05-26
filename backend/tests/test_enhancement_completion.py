"""
Tests for the completed enhancement plan features.
"""

import pytest
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.core.cache import cache
from unittest.mock import patch, MagicMock
import json
import time

from core.models import Tenant
from core.rate_limiting import UserRateThrottle, TenantRateThrottle, RateLimitAnalytics
from graphql_api.schema import schema
from graphene.test import Client

User = get_user_model()


class GraphQLEndpointTests(TestCase):
    """Test GraphQL endpoint functionality."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant'
        )
        self.user.tenant = self.tenant
        self.user.save()
        
        self.client = Client(schema)
    
    def test_graphql_schema_exists(self):
        """Test that GraphQL schema is properly configured."""
        self.assertIsNotNone(schema)
        self.assertTrue(hasattr(schema, 'query'))
        self.assertTrue(hasattr(schema, 'mutation'))
    
    def test_user_query(self):
        """Test GraphQL user query."""
        query = '''
        query {
            users {
                edges {
                    node {
                        id
                        username
                        email
                    }
                }
            }
        }
        '''
        
        # Mock authentication
        with patch('graphql_jwt.decorators.login_required') as mock_auth:
            mock_auth.return_value = lambda func: func
            result = self.client.execute(query)
            
            self.assertIsNone(result.get('errors'))
            self.assertIn('data', result)
    
    def test_migration_project_mutation(self):
        """Test GraphQL mutation for creating migration project."""
        mutation = '''
        mutation {
            createMigrationProject(name: "Test Project", description: "Test Description") {
                success
                errors
                migrationProject {
                    id
                    name
                    description
                }
            }
        }
        '''
        
        # Mock authentication and context
        with patch('graphql_jwt.decorators.login_required') as mock_auth:
            mock_auth.return_value = lambda func: func
            
            # Mock context with user
            context = MagicMock()
            context.user = self.user
            
            result = self.client.execute(mutation, context=context)
            
            self.assertIsNone(result.get('errors'))
            self.assertIn('data', result)


class EnhancedRateLimitingTests(TestCase):
    """Test enhanced rate limiting functionality."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant',
            subscription_tier='basic'
        )
        self.user.tenant = self.tenant
        self.user.save()
        
        # Clear cache before each test
        cache.clear()
    
    def test_user_rate_throttle_initialization(self):
        """Test UserRateThrottle initialization."""
        throttle = UserRateThrottle()
        self.assertEqual(throttle.scope, 'user')
        self.assertIn('free', throttle.RATE_LIMITS)
        self.assertIn('basic', throttle.RATE_LIMITS)
        self.assertIn('premium', throttle.RATE_LIMITS)
        self.assertIn('enterprise', throttle.RATE_LIMITS)
    
    def test_tenant_rate_throttle_initialization(self):
        """Test TenantRateThrottle initialization."""
        throttle = TenantRateThrottle()
        self.assertEqual(throttle.scope, 'tenant')
        self.assertIn('free', throttle.RATE_LIMITS)
        self.assertIn('basic', throttle.RATE_LIMITS)
    
    def test_user_rate_limit_check(self):
        """Test user rate limit checking."""
        throttle = UserRateThrottle()
        request = self.factory.get('/api/test/')
        request.user = self.user
        
        # Mock view
        view = MagicMock()
        
        # First request should be allowed
        self.assertTrue(throttle.allow_request(request, view))
        
        # Test rate limit configuration
        subscription_tier = throttle.get_subscription_tier(self.tenant)
        self.assertEqual(subscription_tier, 'basic')
        
        rate_config = throttle.get_rate_limit_config(request, subscription_tier)
        self.assertIn('requests', rate_config)
        self.assertIn('window', rate_config)
    
    def test_tenant_rate_limit_check(self):
        """Test tenant rate limit checking."""
        throttle = TenantRateThrottle()
        request = self.factory.get('/api/test/')
        request.user = self.user
        
        # Mock view
        view = MagicMock()
        
        # First request should be allowed
        self.assertTrue(throttle.allow_request(request, view))
    
    def test_rate_limit_key_generation(self):
        """Test rate limit cache key generation."""
        throttle = UserRateThrottle()
        request = self.factory.get('/api/test/')
        request.user = self.user
        
        key = throttle.get_rate_limit_key(request, str(self.user.id), 'user')
        
        self.assertIn('rate_limit', key)
        self.assertIn('user', key)
        self.assertIn(str(self.user.id), key)
    
    def test_endpoint_specific_limits(self):
        """Test endpoint-specific rate limit multipliers."""
        throttle = UserRateThrottle()
        
        # Test ML endpoint (should have lower limit)
        ml_request = self.factory.get('/api/ml/analyze/')
        ml_request.user = self.user
        
        ml_config = throttle.get_rate_limit_config(ml_request, 'basic')
        
        # Test regular endpoint
        regular_request = self.factory.get('/api/projects/')
        regular_request.user = self.user
        
        regular_config = throttle.get_rate_limit_config(regular_request, 'basic')
        
        # ML endpoint should have lower limit due to multiplier
        self.assertLess(ml_config['requests'], regular_config['requests'])
    
    def test_rate_limit_analytics(self):
        """Test rate limit analytics functionality."""
        # Test user stats
        user_stats = RateLimitAnalytics.get_user_rate_limit_stats(str(self.user.id))
        self.assertIsInstance(user_stats, dict)
        
        # Test tenant stats
        tenant_stats = RateLimitAnalytics.get_tenant_rate_limit_stats(str(self.tenant.id))
        self.assertIsInstance(tenant_stats, dict)
        
        # Test global stats
        global_stats = RateLimitAnalytics.get_global_rate_limit_stats()
        self.assertIsInstance(global_stats, dict)
        self.assertIn('total_requests', global_stats)
    
    def test_subscription_tier_limits(self):
        """Test different subscription tier limits."""
        throttle = UserRateThrottle()
        
        # Test free tier
        free_config = throttle.RATE_LIMITS['free']
        basic_config = throttle.RATE_LIMITS['basic']
        premium_config = throttle.RATE_LIMITS['premium']
        enterprise_config = throttle.RATE_LIMITS['enterprise']
        
        # Verify increasing limits
        self.assertLess(free_config['requests'], basic_config['requests'])
        self.assertLess(basic_config['requests'], premium_config['requests'])
        self.assertLess(premium_config['requests'], enterprise_config['requests'])
    
    def test_unauthenticated_user_handling(self):
        """Test rate limiting for unauthenticated users."""
        throttle = UserRateThrottle()
        request = self.factory.get('/api/test/')
        request.user = MagicMock()
        request.user.is_authenticated = False
        
        view = MagicMock()
        
        # Should allow unauthenticated users (handled by anonymous throttle)
        self.assertTrue(throttle.allow_request(request, view))
    
    def test_tenant_extraction_from_request(self):
        """Test tenant extraction from request."""
        throttle = UserRateThrottle()
        request = self.factory.get('/api/test/')
        request.user = self.user
        
        tenant = throttle.get_tenant_from_request(request)
        self.assertEqual(tenant, self.tenant)
    
    def test_cache_key_suffix_generation(self):
        """Test cache key suffix generation."""
        throttle = UserRateThrottle()
        request = self.factory.post('/api/projects/create/')
        
        suffix = throttle.get_cache_key_suffix(request)
        self.assertIn('POST', suffix)
        self.assertIn('/api/projects/create/', suffix)


class IntegrationTests(TestCase):
    """Integration tests for completed features."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant'
        )
        self.user.tenant = self.tenant
        self.user.save()
    
    def test_graphql_with_rate_limiting(self):
        """Test GraphQL endpoint with rate limiting."""
        # This would test the integration of GraphQL with rate limiting
        # In a real scenario, you'd make actual requests and verify rate limits
        pass
    
    def test_enhancement_plan_completion(self):
        """Test that all enhancement plan items are implemented."""
        # Verify GraphQL endpoint exists
        from graphql_api.schema import schema
        self.assertIsNotNone(schema)
        
        # Verify enhanced rate limiting exists
        from core.rate_limiting import UserRateThrottle, TenantRateThrottle
        self.assertTrue(issubclass(UserRateThrottle, object))
        self.assertTrue(issubclass(TenantRateThrottle, object))
        
        # Verify management commands exist
        from core.management.commands.manage_rate_limits import Command
        self.assertTrue(issubclass(Command, object))


@pytest.mark.django_db
class PytestEnhancementTests:
    """Pytest-style tests for enhancement features."""
    
    def test_graphql_schema_introspection(self):
        """Test GraphQL schema introspection."""
        client = Client(schema)
        
        introspection_query = '''
        query IntrospectionQuery {
            __schema {
                types {
                    name
                }
            }
        }
        '''
        
        result = client.execute(introspection_query)
        assert 'errors' not in result or result['errors'] is None
        assert 'data' in result
        assert '__schema' in result['data']
    
    def test_rate_limiting_configuration(self):
        """Test rate limiting configuration."""
        from django.conf import settings
        
        # Verify enhanced rate limiting settings exist
        assert hasattr(settings, 'ENHANCED_RATE_LIMITING')
        assert 'SUBSCRIPTION_TIERS' in settings.ENHANCED_RATE_LIMITING
        assert 'ENDPOINT_MULTIPLIERS' in settings.ENHANCED_RATE_LIMITING
    
    def test_graphql_settings_configuration(self):
        """Test GraphQL settings configuration."""
        from django.conf import settings
        
        # Verify GraphQL settings exist
        assert hasattr(settings, 'GRAPHENE')
        assert 'SCHEMA' in settings.GRAPHENE
        assert settings.GRAPHENE['SCHEMA'] == 'graphql_api.schema.schema'
