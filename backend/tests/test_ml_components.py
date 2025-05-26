"""
Comprehensive tests for ML and data processing components.
"""

import pytest
import pandas as pd
import numpy as np
from django.test import TestCase
from unittest.mock import patch, MagicMock, mock_open
import json
import tempfile
import os

from ml.advanced_models import AdvancedSchemaRecognitionModel, DataQualityAssessmentModel
from ml.data_profiling import DataProfiler
from ml.models import MLModel
from analyzer.models import DataSource, Entity, Field


class AdvancedSchemaRecognitionTests(TestCase):
    """Test advanced schema recognition functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.model = AdvancedSchemaRecognitionModel()
        self.sample_schema = [
            {
                'name': 'customers',
                'fields': [
                    {'name': 'customer_id', 'type': 'integer'},
                    {'name': 'first_name', 'type': 'string'},
                    {'name': 'last_name', 'type': 'string'},
                    {'name': 'email', 'type': 'string'},
                    {'name': 'phone', 'type': 'string'},
                    {'name': 'created_date', 'type': 'timestamp'},
                    {'name': 'is_active', 'type': 'boolean'}
                ]
            },
            {
                'name': 'orders',
                'fields': [
                    {'name': 'order_id', 'type': 'integer'},
                    {'name': 'customer_id', 'type': 'integer'},
                    {'name': 'order_date', 'type': 'timestamp'},
                    {'name': 'total_amount', 'type': 'decimal'},
                    {'name': 'status', 'type': 'string'}
                ]
            }
        ]
    
    def test_feature_extraction(self):
        """Test feature extraction from schema data."""
        features = self.model.extract_features(self.sample_schema)
        
        # Check feature matrix dimensions
        self.assertEqual(features.shape[0], 2)  # Two entities
        self.assertGreater(features.shape[1], 10)  # Multiple features
        
        # Check that features are numeric
        self.assertTrue(np.issubdtype(features.dtype, np.number))
    
    def test_heuristic_prediction_customer_entity(self):
        """Test heuristic prediction for customer-like entity."""
        customer_schema = [{
            'name': 'users',
            'fields': [
                {'name': 'user_id', 'type': 'integer'},
                {'name': 'first_name', 'type': 'string'},
                {'name': 'last_name', 'type': 'string'},
                {'name': 'email', 'type': 'string'},
                {'name': 'phone', 'type': 'string'}
            ]
        }]
        
        predictions = self.model._heuristic_prediction(customer_schema)
        
        self.assertEqual(len(predictions), 1)
        self.assertEqual(predictions[0]['entity_name'], 'users')
        self.assertEqual(predictions[0]['predicted_type'], 'person')
        self.assertGreater(predictions[0]['confidence'], 0.5)
    
    def test_heuristic_prediction_transaction_entity(self):
        """Test heuristic prediction for transaction-like entity."""
        transaction_schema = [{
            'name': 'payments',
            'fields': [
                {'name': 'payment_id', 'type': 'integer'},
                {'name': 'amount', 'type': 'decimal'},
                {'name': 'payment_date', 'type': 'timestamp'},
                {'name': 'currency', 'type': 'string'},
                {'name': 'status', 'type': 'string'}
            ]
        }]
        
        predictions = self.model._heuristic_prediction(transaction_schema)
        
        self.assertEqual(len(predictions), 1)
        self.assertEqual(predictions[0]['entity_name'], 'payments')
        self.assertEqual(predictions[0]['predicted_type'], 'transaction')
        self.assertGreater(predictions[0]['confidence'], 0.5)
    
    def test_predict_schema_types(self):
        """Test complete schema type prediction."""
        predictions = self.model.predict_schema_types(self.sample_schema)
        
        self.assertEqual(len(predictions), 2)
        
        # Check customer entity prediction
        customer_pred = next(p for p in predictions if p['entity_name'] == 'customers')
        self.assertEqual(customer_pred['predicted_type'], 'person')
        
        # Check order entity prediction
        order_pred = next(p for p in predictions if p['entity_name'] == 'orders')
        self.assertEqual(order_pred['predicted_type'], 'transaction')
    
    def test_empty_schema_handling(self):
        """Test handling of empty schema data."""
        predictions = self.model.predict_schema_types([])
        self.assertEqual(predictions, [])
    
    def test_malformed_schema_handling(self):
        """Test handling of malformed schema data."""
        malformed_schema = [
            {
                'name': 'incomplete_entity'
                # Missing 'fields' key
            }
        ]
        
        # Should not raise exception, should handle gracefully
        predictions = self.model.predict_schema_types(malformed_schema)
        self.assertEqual(len(predictions), 1)
        self.assertEqual(predictions[0]['predicted_type'], 'unknown')


class DataQualityAssessmentTests(TestCase):
    """Test data quality assessment functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.model = DataQualityAssessmentModel()
        
        # Create test DataFrame with various data quality issues
        self.test_data = pd.DataFrame({
            'id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'name': ['Alice', 'Bob', None, 'David', 'Eve', 'Frank', 'Grace', 'Henry', 'Ivy', 'Jack'],
            'email': [
                'alice@test.com', 'bob@test.com', 'invalid-email', 'david@test.com',
                'eve@test.com', 'frank@test.com', 'grace@test.com', 'henry@test.com',
                'ivy@test.com', 'jack@test.com'
            ],
            'age': [25, 30, 35, 40, 45, 50, 55, 60, 65, 70],
            'score': [85.5, 92.0, 78.5, 88.0, 95.5, 82.0, 90.0, 87.5, 93.0, 89.0],
            'duplicate_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 1]  # Has duplicate
        })
    
    def test_assess_data_quality(self):
        """Test comprehensive data quality assessment."""
        quality_report = self.model.assess_data_quality(self.test_data)
        
        # Check main sections exist
        required_sections = [
            'overall_score', 'completeness', 'consistency', 
            'accuracy', 'validity', 'uniqueness', 'recommendations'
        ]
        for section in required_sections:
            self.assertIn(section, quality_report)
    
    def test_completeness_assessment(self):
        """Test completeness assessment."""
        quality_report = self.model.assess_data_quality(self.test_data)
        completeness = quality_report['completeness']
        
        self.assertIn('score', completeness)
        self.assertIn('missing_cells', completeness)
        self.assertIn('missing_percentage', completeness)
        self.assertIn('columns_with_missing', completeness)
        
        # Should detect missing value in 'name' column
        self.assertEqual(completeness['missing_cells'], 1)
        self.assertIn('name', completeness['columns_with_missing'])
    
    def test_uniqueness_assessment(self):
        """Test uniqueness assessment."""
        quality_report = self.model.assess_data_quality(self.test_data)
        uniqueness = quality_report['uniqueness']
        
        self.assertIn('score', uniqueness)
        self.assertIn('duplicate_rows', uniqueness)
        self.assertIn('columns_with_duplicates', uniqueness)
        
        # Should detect duplicates in 'duplicate_id' column
        self.assertIn('duplicate_id', uniqueness['columns_with_duplicates'])
    
    def test_validity_assessment(self):
        """Test validity assessment."""
        quality_report = self.model.assess_data_quality(self.test_data)
        validity = quality_report['validity']
        
        self.assertIn('score', validity)
        self.assertIn('invalid_emails', validity)
        
        # Should detect invalid email
        self.assertGreater(validity['invalid_emails'], 0)
    
    def test_consistency_assessment(self):
        """Test consistency assessment."""
        quality_report = self.model.assess_data_quality(self.test_data)
        consistency = quality_report['consistency']
        
        self.assertIn('score', consistency)
        self.assertIn('data_type_consistency', consistency)
    
    def test_accuracy_assessment(self):
        """Test accuracy assessment."""
        quality_report = self.model.assess_data_quality(self.test_data)
        accuracy = quality_report['accuracy']
        
        self.assertIn('score', accuracy)
        self.assertIn('outliers_detected', accuracy)
    
    def test_recommendations_generation(self):
        """Test quality improvement recommendations."""
        quality_report = self.model.assess_data_quality(self.test_data)
        recommendations = quality_report['recommendations']
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Should recommend fixing missing values
        missing_rec = any('missing' in rec.lower() for rec in recommendations)
        self.assertTrue(missing_rec)
    
    def test_empty_dataframe_handling(self):
        """Test handling of empty DataFrame."""
        empty_df = pd.DataFrame()
        quality_report = self.model.assess_data_quality(empty_df)
        
        self.assertEqual(quality_report['overall_score'], 0.0)
        self.assertIn('Dataset is empty', quality_report['recommendations'])


class DataProfilingTests(TestCase):
    """Test data profiling functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.profiler = DataProfiler()
        
        # Create comprehensive test dataset
        np.random.seed(42)  # For reproducible results
        self.test_data = pd.DataFrame({
            'customer_id': range(1, 101),
            'name': [f'Customer {i}' for i in range(1, 101)],
            'age': np.random.randint(18, 80, 100),
            'email': [f'customer{i}@example.com' for i in range(1, 101)],
            'registration_date': pd.date_range('2020-01-01', periods=100, freq='D'),
            'is_active': np.random.choice([True, False], 100),
            'score': np.random.normal(75, 15, 100),
            'category': np.random.choice(['A', 'B', 'C'], 100),
            'salary': np.random.lognormal(10, 1, 100)
        })
    
    def test_profile_dataset_structure(self):
        """Test dataset profiling structure."""
        profile = self.profiler.profile_dataset(self.test_data)
        
        # Check main sections
        required_sections = [
            'dataset_info', 'column_profiles', 'data_types',
            'relationships', 'patterns', 'quality_metrics',
            'statistical_summary', 'recommendations'
        ]
        for section in required_sections:
            self.assertIn(section, profile)
    
    def test_dataset_info_profiling(self):
        """Test dataset info profiling."""
        profile = self.profiler.profile_dataset(self.test_data)
        dataset_info = profile['dataset_info']
        
        self.assertEqual(dataset_info['total_rows'], 100)
        self.assertEqual(dataset_info['total_columns'], 9)
        self.assertIn('memory_usage', dataset_info)
        self.assertIn('file_size_estimate', dataset_info)
    
    def test_numeric_column_profiling(self):
        """Test numeric column profiling."""
        profile = self.profiler.profile_dataset(self.test_data)
        age_profile = profile['column_profiles']['age']
        
        self.assertEqual(age_profile['profile_type'], 'numeric')
        self.assertIn('min', age_profile)
        self.assertIn('max', age_profile)
        self.assertIn('mean', age_profile)
        self.assertIn('median', age_profile)
        self.assertIn('std', age_profile)
        self.assertIn('quartiles', age_profile)
        self.assertIn('outliers', age_profile)
    
    def test_text_column_profiling(self):
        """Test text column profiling."""
        profile = self.profiler.profile_dataset(self.test_data)
        name_profile = profile['column_profiles']['name']
        
        self.assertEqual(name_profile['profile_type'], 'text')
        self.assertIn('min_length', name_profile)
        self.assertIn('max_length', name_profile)
        self.assertIn('avg_length', name_profile)
        self.assertIn('unique_values', name_profile)
        self.assertIn('most_common', name_profile)
    
    def test_datetime_column_profiling(self):
        """Test datetime column profiling."""
        profile = self.profiler.profile_dataset(self.test_data)
        date_profile = profile['column_profiles']['registration_date']
        
        self.assertEqual(date_profile['profile_type'], 'datetime')
        self.assertIn('min_date', date_profile)
        self.assertIn('max_date', date_profile)
        self.assertIn('date_range', date_profile)
        self.assertIn('frequency_analysis', date_profile)
    
    def test_boolean_column_profiling(self):
        """Test boolean column profiling."""
        profile = self.profiler.profile_dataset(self.test_data)
        active_profile = profile['column_profiles']['is_active']
        
        self.assertEqual(active_profile['profile_type'], 'boolean')
        self.assertIn('true_count', active_profile)
        self.assertIn('false_count', active_profile)
        self.assertIn('true_percentage', active_profile)
    
    def test_categorical_column_profiling(self):
        """Test categorical column profiling."""
        profile = self.profiler.profile_dataset(self.test_data)
        category_profile = profile['column_profiles']['category']
        
        self.assertEqual(category_profile['profile_type'], 'categorical')
        self.assertIn('unique_values', category_profile)
        self.assertIn('value_counts', category_profile)
        self.assertIn('most_common', category_profile)
    
    def test_correlation_analysis(self):
        """Test correlation analysis."""
        profile = self.profiler.profile_dataset(self.test_data)
        relationships = profile['relationships']
        
        self.assertIn('correlations', relationships)
        self.assertIn('strong_correlations', relationships)
    
    def test_pattern_detection(self):
        """Test pattern detection."""
        profile = self.profiler.profile_dataset(self.test_data)
        patterns = profile['patterns']
        
        self.assertIn('email_patterns', patterns)
        self.assertIn('date_patterns', patterns)
        self.assertIn('numeric_patterns', patterns)
    
    def test_sampling_large_dataset(self):
        """Test profiling with sampling for large datasets."""
        # Create larger dataset
        large_data = pd.DataFrame({
            'id': range(10000),
            'value': np.random.random(10000)
        })
        
        profile = self.profiler.profile_dataset(large_data, sample_size=1000)
        
        # Should still provide meaningful results
        self.assertEqual(profile['dataset_info']['total_rows'], 10000)
        self.assertIn('sampling_info', profile['dataset_info'])
        self.assertEqual(profile['dataset_info']['sampling_info']['sample_size'], 1000)


class MLModelManagementTests(TestCase):
    """Test ML model management functionality."""
    
    def test_create_ml_model_record(self):
        """Test creating ML model database record."""
        model = MLModel.objects.create(
            name='Test Schema Recognition Model',
            model_type='SCHEMA_RECOGNITION',
            description='Test model for schema recognition',
            version='1.0.0',
            file_path='/models/schema_recognition_v1.pkl',
            is_active=True
        )
        
        self.assertEqual(model.name, 'Test Schema Recognition Model')
        self.assertEqual(model.model_type, 'SCHEMA_RECOGNITION')
        self.assertEqual(model.version, '1.0.0')
        self.assertTrue(model.is_active)
    
    def test_ml_model_str_representation(self):
        """Test ML model string representation."""
        model = MLModel.objects.create(
            name='Test Model',
            model_type='DATA_QUALITY',
            version='2.1.0',
            file_path='/models/test_model.pkl'
        )
        
        expected = 'Test Model v2.1.0'
        self.assertEqual(str(model), expected)


@pytest.mark.django_db
class MLIntegrationTests:
    """Integration tests for ML components."""
    
    def test_schema_recognition_with_database_entities(self):
        """Test schema recognition with actual database entities."""
        # Create test data source and entities
        data_source = DataSource.objects.create(
            name='Test Database',
            source_type='postgresql'
        )
        
        customer_entity = Entity.objects.create(
            data_source=data_source,
            name='customers',
            original_name='customers'
        )
        
        # Create fields
        Field.objects.create(
            entity=customer_entity,
            name='customer_id',
            original_name='customer_id',
            data_type='integer',
            is_primary_key=True
        )
        Field.objects.create(
            entity=customer_entity,
            name='email',
            original_name='email',
            data_type='string'
        )
        Field.objects.create(
            entity=customer_entity,
            name='first_name',
            original_name='first_name',
            data_type='string'
        )
        
        # Convert to schema format
        schema_data = [{
            'name': customer_entity.name,
            'fields': [
                {
                    'name': field.name,
                    'type': field.data_type
                }
                for field in customer_entity.fields.all()
            ]
        }]
        
        # Test schema recognition
        model = AdvancedSchemaRecognitionModel()
        predictions = model.predict_schema_types(schema_data)
        
        assert len(predictions) == 1
        assert predictions[0]['entity_name'] == 'customers'
        assert predictions[0]['predicted_type'] == 'person'
    
    def test_data_quality_assessment_integration(self):
        """Test data quality assessment integration."""
        # Create test DataFrame
        test_data = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', None, 'David', 'Eve'],
            'email': ['alice@test.com', 'bob@test.com', 'invalid', 'david@test.com', 'eve@test.com']
        })
        
        # Assess quality
        model = DataQualityAssessmentModel()
        quality_report = model.assess_data_quality(test_data)
        
        # Verify results
        assert quality_report['completeness']['missing_cells'] == 1
        assert quality_report['validity']['invalid_emails'] == 1
        assert len(quality_report['recommendations']) > 0
