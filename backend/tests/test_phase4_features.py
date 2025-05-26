"""
Comprehensive tests for Phase 4 features.
"""

import pytest
import json
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

from core.models import Tenant
from integrations.models import CloudProvider, CloudDataSource, CloudMigrationJob
from integrations.aws_service import AWSService
from ml.advanced_models import AdvancedSchemaRecognitionModel, DataQualityAssessmentModel
from ml.data_profiling import DataProfiler


class CloudIntegrationTests(APITestCase):
    """Tests for cloud integration features."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant',
            is_active=True
        )
        self.client.force_authenticate(user=self.user)
    
    def test_create_cloud_provider(self):
        """Test creating a cloud provider."""
        data = {
            'name': 'Test AWS Provider',
            'provider': 'aws',
            'tenant': self.tenant.id,
            'region': 'us-east-1',
            'access_key': 'test_access_key',
            'secret_key': 'test_secret_key',
            'config': {
                'use_ssl': True,
                'timeout': 30
            }
        }
        
        response = self.client.post('/api/integrations/providers/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CloudProvider.objects.count(), 1)
        
        provider = CloudProvider.objects.first()
        self.assertEqual(provider.name, 'Test AWS Provider')
        self.assertEqual(provider.provider, 'aws')
    
    def test_create_cloud_data_source(self):
        """Test creating a cloud data source."""
        provider = CloudProvider.objects.create(
            name='Test Provider',
            provider='aws',
            tenant=self.tenant,
            region='us-east-1'
        )
        
        data = {
            'name': 'Test S3 Source',
            'source_type': 's3',
            'provider': provider.id,
            'bucket_name': 'test-bucket',
            'file_path': 'data/customers.csv',
            'file_format': 'csv'
        }
        
        response = self.client.post('/api/integrations/data-sources/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CloudDataSource.objects.count(), 1)
    
    @patch('integrations.aws_service.boto3.Session')
    def test_aws_service_connection(self, mock_session):
        """Test AWS service connection."""
        # Mock AWS session and STS client
        mock_sts = MagicMock()
        mock_sts.get_caller_identity.return_value = {
            'Account': '123456789012',
            'UserId': 'AIDACKCEVSQ6C2EXAMPLE',
            'Arn': 'arn:aws:iam::123456789012:user/testuser'
        }
        mock_session.return_value.client.return_value = mock_sts
        
        config = {
            'access_key': 'test_key',
            'secret_key': 'test_secret',
            'region': 'us-east-1'
        }
        
        aws_service = AWSService(config)
        result = aws_service.test_connection()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['account_id'], '123456789012')
    
    @patch('integrations.aws_service.boto3.Session')
    def test_aws_list_s3_buckets(self, mock_session):
        """Test listing S3 buckets."""
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_s3.list_buckets.return_value = {
            'Buckets': [
                {'Name': 'test-bucket-1', 'CreationDate': '2024-01-01T00:00:00Z'},
                {'Name': 'test-bucket-2', 'CreationDate': '2024-01-02T00:00:00Z'}
            ]
        }
        mock_s3.get_bucket_location.return_value = {'LocationConstraint': 'us-west-2'}
        mock_session.return_value.client.return_value = mock_s3
        
        config = {
            'access_key': 'test_key',
            'secret_key': 'test_secret',
            'region': 'us-east-1'
        }
        
        aws_service = AWSService(config)
        buckets = aws_service.list_s3_buckets()
        
        self.assertEqual(len(buckets), 2)
        self.assertEqual(buckets[0]['name'], 'test-bucket-1')
        self.assertEqual(buckets[1]['name'], 'test-bucket-2')


class AdvancedMLTests(TestCase):
    """Tests for advanced ML features."""
    
    def setUp(self):
        """Set up test data."""
        self.schema_model = AdvancedSchemaRecognitionModel()
        self.quality_model = DataQualityAssessmentModel()
        self.profiler = DataProfiler()
    
    def test_schema_recognition_feature_extraction(self):
        """Test schema recognition feature extraction."""
        schema_data = [
            {
                'name': 'customers',
                'fields': [
                    {'name': 'customer_id', 'type': 'integer'},
                    {'name': 'first_name', 'type': 'string'},
                    {'name': 'last_name', 'type': 'string'},
                    {'name': 'email', 'type': 'string'},
                    {'name': 'phone', 'type': 'string'},
                    {'name': 'created_date', 'type': 'timestamp'}
                ]
            }
        ]
        
        features = self.schema_model.extract_features(schema_data)
        
        self.assertEqual(features.shape[0], 1)  # One entity
        self.assertGreater(features.shape[1], 10)  # Multiple features
    
    def test_schema_recognition_heuristic_prediction(self):
        """Test heuristic schema recognition prediction."""
        schema_data = [
            {
                'name': 'users',
                'fields': [
                    {'name': 'user_id', 'type': 'integer'},
                    {'name': 'first_name', 'type': 'string'},
                    {'name': 'email', 'type': 'string'}
                ]
            }
        ]
        
        predictions = self.schema_model._heuristic_prediction(schema_data)
        
        self.assertEqual(len(predictions), 1)
        self.assertEqual(predictions[0]['entity_name'], 'users')
        self.assertEqual(predictions[0]['predicted_type'], 'person')
        self.assertGreater(predictions[0]['confidence'], 0)
    
    def test_data_quality_assessment(self):
        """Test data quality assessment."""
        # Create test DataFrame
        data = {
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', None, 'David', 'Eve'],
            'age': [25, 30, 35, 40, 45],
            'email': ['alice@test.com', 'bob@test.com', 'invalid-email', 'david@test.com', 'eve@test.com'],
            'score': [85.5, 92.0, 78.5, 88.0, 95.5]
        }
        df = pd.DataFrame(data)
        
        quality_report = self.quality_model.assess_data_quality(df)
        
        self.assertIn('overall_score', quality_report)
        self.assertIn('completeness', quality_report)
        self.assertIn('consistency', quality_report)
        self.assertIn('accuracy', quality_report)
        self.assertIn('validity', quality_report)
        self.assertIn('uniqueness', quality_report)
        self.assertIn('recommendations', quality_report)
        
        # Check completeness assessment
        completeness = quality_report['completeness']
        self.assertLess(completeness['score'], 1.0)  # Should detect missing value
        self.assertEqual(completeness['missing_cells'], 1)
    
    def test_data_profiling(self):
        """Test comprehensive data profiling."""
        # Create test DataFrame
        data = {
            'customer_id': range(1, 101),
            'name': [f'Customer {i}' for i in range(1, 101)],
            'age': np.random.randint(18, 80, 100),
            'email': [f'customer{i}@example.com' for i in range(1, 101)],
            'registration_date': pd.date_range('2020-01-01', periods=100, freq='D'),
            'is_active': np.random.choice([True, False], 100),
            'score': np.random.normal(75, 15, 100)
        }
        df = pd.DataFrame(data)
        
        profile = self.profiler.profile_dataset(df)
        
        # Check main sections
        self.assertIn('dataset_info', profile)
        self.assertIn('column_profiles', profile)
        self.assertIn('data_types', profile)
        self.assertIn('relationships', profile)
        self.assertIn('patterns', profile)
        self.assertIn('quality_metrics', profile)
        self.assertIn('statistical_summary', profile)
        self.assertIn('recommendations', profile)
        
        # Check dataset info
        dataset_info = profile['dataset_info']
        self.assertEqual(dataset_info['total_rows'], 100)
        self.assertEqual(dataset_info['total_columns'], 7)
        
        # Check column profiles
        column_profiles = profile['column_profiles']
        self.assertEqual(len(column_profiles), 7)
        
        # Check numeric column profiling
        age_profile = column_profiles['age']
        self.assertEqual(age_profile['profile_type'], 'numeric')
        self.assertIn('min', age_profile)
        self.assertIn('max', age_profile)
        self.assertIn('mean', age_profile)
        
        # Check text column profiling
        name_profile = column_profiles['name']
        self.assertEqual(name_profile['profile_type'], 'text')
        self.assertIn('min_length', name_profile)
        self.assertIn('max_length', name_profile)
        
        # Check datetime column profiling
        date_profile = column_profiles['registration_date']
        self.assertEqual(date_profile['profile_type'], 'datetime')
        self.assertIn('min_date', date_profile)
        self.assertIn('max_date', date_profile)
        
        # Check boolean column profiling
        active_profile = column_profiles['is_active']
        self.assertEqual(active_profile['profile_type'], 'boolean')
        self.assertIn('true_count', active_profile)
        self.assertIn('false_count', active_profile)


class PWAFeatureTests(TestCase):
    """Tests for PWA features."""
    
    def test_service_worker_exists(self):
        """Test that service worker file exists and is accessible."""
        # This would test the service worker endpoint
        # In a real implementation, you'd test the actual service worker functionality
        pass
    
    def test_manifest_json_format(self):
        """Test that manifest.json has correct format."""
        # This would validate the manifest.json structure
        pass
    
    def test_offline_functionality(self):
        """Test offline functionality."""
        # This would test caching and offline capabilities
        pass


class APIDocumentationTests(APITestCase):
    """Tests for API documentation features."""
    
    def test_swagger_ui_accessible(self):
        """Test that Swagger UI is accessible."""
        response = self.client.get('/api/docs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_redoc_accessible(self):
        """Test that ReDoc is accessible."""
        response = self.client.get('/api/redoc/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_openapi_schema(self):
        """Test OpenAPI schema generation."""
        response = self.client.get('/api/schema/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Validate schema structure
        schema = response.json()
        self.assertIn('openapi', schema)
        self.assertIn('info', schema)
        self.assertIn('paths', schema)
        self.assertIn('components', schema)
    
    def test_api_versioning(self):
        """Test API versioning in documentation."""
        response = self.client.get('/api/schema/')
        schema = response.json()
        
        # Check that version is specified
        self.assertIn('version', schema['info'])


class IntegrationTests(TransactionTestCase):
    """Integration tests for Phase 4 features."""
    
    def setUp(self):
        """Set up integration test data."""
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@example.com',
            password='testpass123'
        )
        self.tenant = Tenant.objects.create(
            name='Integration Tenant',
            slug='integration-tenant',
            is_active=True
        )
    
    def test_end_to_end_cloud_migration(self):
        """Test end-to-end cloud migration workflow."""
        # This would test the complete workflow:
        # 1. Create cloud provider
        # 2. Create data sources
        # 3. Create migration job
        # 4. Execute migration
        # 5. Monitor progress
        # 6. Validate results
        pass
    
    def test_ml_pipeline_integration(self):
        """Test ML pipeline integration."""
        # This would test:
        # 1. Data profiling
        # 2. Schema recognition
        # 3. Quality assessment
        # 4. Recommendations generation
        pass
    
    def test_pwa_offline_sync(self):
        """Test PWA offline synchronization."""
        # This would test:
        # 1. Offline data caching
        # 2. Background sync
        # 3. Conflict resolution
        pass


class PerformanceTests(TestCase):
    """Performance tests for Phase 4 features."""
    
    def test_large_dataset_profiling_performance(self):
        """Test data profiling performance with large datasets."""
        # Create large test dataset
        size = 10000
        data = {
            'id': range(size),
            'value': np.random.random(size),
            'category': np.random.choice(['A', 'B', 'C'], size),
            'timestamp': pd.date_range('2020-01-01', periods=size, freq='H')
        }
        df = pd.DataFrame(data)
        
        profiler = DataProfiler()
        
        import time
        start_time = time.time()
        profile = profiler.profile_dataset(df, sample_size=1000)
        end_time = time.time()
        
        # Should complete within reasonable time
        self.assertLess(end_time - start_time, 10.0)  # 10 seconds max
        self.assertIsNotNone(profile)
    
    def test_ml_model_prediction_performance(self):
        """Test ML model prediction performance."""
        model = AdvancedSchemaRecognitionModel()
        
        # Create large schema data
        schema_data = []
        for i in range(100):
            schema_data.append({
                'name': f'table_{i}',
                'fields': [
                    {'name': f'field_{j}', 'type': 'string'} 
                    for j in range(10)
                ]
            })
        
        import time
        start_time = time.time()
        predictions = model._heuristic_prediction(schema_data)
        end_time = time.time()
        
        # Should complete within reasonable time
        self.assertLess(end_time - start_time, 5.0)  # 5 seconds max
        self.assertEqual(len(predictions), 100)


# Test utilities
class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_sample_dataframe(rows=100):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame({
            'id': range(rows),
            'name': [f'Item {i}' for i in range(rows)],
            'value': np.random.random(rows),
            'category': np.random.choice(['A', 'B', 'C'], rows),
            'date': pd.date_range('2020-01-01', periods=rows, freq='D'),
            'is_active': np.random.choice([True, False], rows)
        })
    
    @staticmethod
    def create_cloud_provider_data():
        """Create sample cloud provider data."""
        return {
            'name': 'Test Provider',
            'provider': 'aws',
            'region': 'us-east-1',
            'access_key': 'test_key',
            'secret_key': 'test_secret',
            'config': {'timeout': 30}
        }
    
    @staticmethod
    def create_schema_data():
        """Create sample schema data."""
        return [
            {
                'name': 'customers',
                'fields': [
                    {'name': 'id', 'type': 'integer'},
                    {'name': 'name', 'type': 'string'},
                    {'name': 'email', 'type': 'string'}
                ]
            }
        ]
