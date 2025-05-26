"""
Integration tests for complete MigrateIQ workflows.
"""

import pytest
import json
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

from core.models import Tenant, UserProfile
from analyzer.models import DataSource, Entity, Field
from orchestrator.models import MigrationProject, MigrationTask
from mapping_engine.models import Mapping, FieldMapping
from transformation.models import TransformationRule, TransformationJob
from validation.models import ValidationRule, ValidationResult
from ml.advanced_models import AdvancedSchemaRecognitionModel, DataQualityAssessmentModel
from ml.data_profiling import DataProfiler

User = get_user_model()


class EndToEndMigrationWorkflowTests(TransactionTestCase):
    """Test complete end-to-end migration workflows."""
    
    def setUp(self):
        """Set up test data for integration tests."""
        self.tenant = Tenant.objects.create(
            name='Integration Test Tenant',
            slug='integration-tenant',
            subscription_tier='premium'
        )
        
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@example.com',
            password='testpass123'
        )
        
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            tenant=self.tenant,
            role='admin'
        )
        
        # Create source and target data sources
        self.source_db = DataSource.objects.create(
            name='Legacy CRM Database',
            source_type='postgresql',
            connection_string='postgresql://user:pass@legacy-db:5432/crm'
        )
        
        self.target_db = DataSource.objects.create(
            name='New CRM Database',
            source_type='postgresql',
            connection_string='postgresql://user:pass@new-db:5432/crm'
        )
        
        # Create source entities and fields
        self.source_customer_entity = Entity.objects.create(
            data_source=self.source_db,
            name='legacy_customers',
            original_name='customers',
            record_count=10000,
            description='Legacy customer data'
        )
        
        # Create source fields
        self.source_fields = [
            Field.objects.create(
                entity=self.source_customer_entity,
                name='cust_id',
                original_name='cust_id',
                data_type='integer',
                is_primary_key=True,
                is_nullable=False
            ),
            Field.objects.create(
                entity=self.source_customer_entity,
                name='fname',
                original_name='fname',
                data_type='string',
                is_nullable=True
            ),
            Field.objects.create(
                entity=self.source_customer_entity,
                name='lname',
                original_name='lname',
                data_type='string',
                is_nullable=True
            ),
            Field.objects.create(
                entity=self.source_customer_entity,
                name='email_addr',
                original_name='email_addr',
                data_type='string',
                is_nullable=True
            ),
            Field.objects.create(
                entity=self.source_customer_entity,
                name='create_dt',
                original_name='create_dt',
                data_type='timestamp',
                is_nullable=False
            )
        ]
        
        # Create target entities and fields
        self.target_customer_entity = Entity.objects.create(
            data_source=self.target_db,
            name='customers',
            original_name='customers',
            description='New customer data structure'
        )
        
        self.target_fields = [
            Field.objects.create(
                entity=self.target_customer_entity,
                name='customer_id',
                original_name='customer_id',
                data_type='integer',
                is_primary_key=True,
                is_nullable=False
            ),
            Field.objects.create(
                entity=self.target_customer_entity,
                name='first_name',
                original_name='first_name',
                data_type='string',
                is_nullable=False
            ),
            Field.objects.create(
                entity=self.target_customer_entity,
                name='last_name',
                original_name='last_name',
                data_type='string',
                is_nullable=False
            ),
            Field.objects.create(
                entity=self.target_customer_entity,
                name='email',
                original_name='email',
                data_type='string',
                is_nullable=False
            ),
            Field.objects.create(
                entity=self.target_customer_entity,
                name='created_at',
                original_name='created_at',
                data_type='timestamp',
                is_nullable=False
            )
        ]
    
    def test_complete_migration_workflow(self):
        """Test complete migration workflow from start to finish."""
        # Step 1: Create migration project
        project = MigrationProject.objects.create(
            name='Legacy CRM Migration',
            description='Migrate customer data from legacy CRM to new system',
            source_system='Legacy CRM',
            target_system='New CRM',
            status='DRAFT'
        )
        
        # Step 2: Create migration tasks
        analysis_task = MigrationTask.objects.create(
            project=project,
            name='Analyze Source Data',
            task_type='ANALYSIS',
            status='PENDING'
        )
        
        mapping_task = MigrationTask.objects.create(
            project=project,
            name='Create Data Mappings',
            task_type='MAPPING',
            status='PENDING'
        )
        
        transformation_task = MigrationTask.objects.create(
            project=project,
            name='Transform Data',
            task_type='TRANSFORMATION',
            status='PENDING'
        )
        
        validation_task = MigrationTask.objects.create(
            project=project,
            name='Validate Data',
            task_type='VALIDATION',
            status='PENDING'
        )
        
        migration_task = MigrationTask.objects.create(
            project=project,
            name='Migrate Data',
            task_type='MIGRATION',
            status='PENDING'
        )
        
        # Step 3: Execute analysis phase
        analysis_task.status = 'IN_PROGRESS'
        analysis_task.save()
        
        # Simulate data profiling
        profiler = DataProfiler()
        sample_data = pd.DataFrame({
            'cust_id': range(1, 101),
            'fname': [f'FirstName{i}' for i in range(1, 101)],
            'lname': [f'LastName{i}' for i in range(1, 101)],
            'email_addr': [f'user{i}@example.com' for i in range(1, 101)],
            'create_dt': pd.date_range('2020-01-01', periods=100, freq='D')
        })
        
        profile = profiler.profile_dataset(sample_data)
        self.assertIn('dataset_info', profile)
        self.assertEqual(profile['dataset_info']['total_rows'], 100)
        
        analysis_task.status = 'COMPLETED'
        analysis_task.save()
        
        # Step 4: Create mappings
        mapping_task.status = 'IN_PROGRESS'
        mapping_task.save()
        
        entity_mapping = Mapping.objects.create(
            source_entity=self.source_customer_entity,
            target_entity=self.target_customer_entity,
            mapping_type='ENTITY',
            confidence_score=0.95
        )
        
        # Create field mappings
        field_mappings = [
            FieldMapping.objects.create(
                entity_mapping=entity_mapping,
                source_field=self.source_fields[0],  # cust_id
                target_field=self.target_fields[0],  # customer_id
                mapping_type='DIRECT',
                confidence_score=1.0
            ),
            FieldMapping.objects.create(
                entity_mapping=entity_mapping,
                source_field=self.source_fields[1],  # fname
                target_field=self.target_fields[1],  # first_name
                mapping_type='DIRECT',
                confidence_score=0.98
            ),
            FieldMapping.objects.create(
                entity_mapping=entity_mapping,
                source_field=self.source_fields[2],  # lname
                target_field=self.target_fields[2],  # last_name
                mapping_type='DIRECT',
                confidence_score=0.98
            ),
            FieldMapping.objects.create(
                entity_mapping=entity_mapping,
                source_field=self.source_fields[3],  # email_addr
                target_field=self.target_fields[3],  # email
                mapping_type='DIRECT',
                confidence_score=0.95
            ),
            FieldMapping.objects.create(
                entity_mapping=entity_mapping,
                source_field=self.source_fields[4],  # create_dt
                target_field=self.target_fields[4],  # created_at
                mapping_type='DIRECT',
                confidence_score=0.99
            )
        ]
        
        mapping_task.status = 'COMPLETED'
        mapping_task.save()
        
        # Step 5: Create transformation rules
        transformation_task.status = 'IN_PROGRESS'
        transformation_task.save()
        
        # Add transformation rule for email field (lowercase)
        email_transform = TransformationRule.objects.create(
            field_mapping=field_mappings[3],  # email mapping
            rule_type='CUSTOM_FUNCTION',
            rule_definition={
                'function': 'lowercase',
                'description': 'Convert email to lowercase'
            },
            order=1
        )
        
        transformation_task.status = 'COMPLETED'
        transformation_task.save()
        
        # Step 6: Create validation rules
        validation_task.status = 'IN_PROGRESS'
        validation_task.save()
        
        # Email validation rule
        email_validation = ValidationRule.objects.create(
            entity=self.target_customer_entity,
            field=self.target_fields[3],  # email field
            rule_type='REGEX',
            rule_definition={
                'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                'message': 'Invalid email format'
            },
            severity='ERROR'
        )
        
        # Required field validation
        required_validation = ValidationRule.objects.create(
            entity=self.target_customer_entity,
            field=self.target_fields[1],  # first_name field
            rule_type='NOT_NULL',
            rule_definition={
                'message': 'First name is required'
            },
            severity='ERROR'
        )
        
        validation_task.status = 'COMPLETED'
        validation_task.save()
        
        # Step 7: Execute migration
        migration_task.status = 'IN_PROGRESS'
        migration_task.save()
        
        # Create transformation job
        transformation_job = TransformationJob.objects.create(
            project=project,
            entity_mapping=entity_mapping,
            status='PENDING'
        )
        
        # Simulate successful transformation
        transformation_job.status = 'COMPLETED'
        transformation_job.records_processed = 10000
        transformation_job.records_succeeded = 9950
        transformation_job.records_failed = 50
        transformation_job.save()
        
        migration_task.status = 'COMPLETED'
        migration_task.save()
        
        # Step 8: Update project status
        project.status = 'COMPLETED'
        project.save()
        
        # Verify workflow completion
        self.assertEqual(project.status, 'COMPLETED')
        self.assertEqual(project.tasks.filter(status='COMPLETED').count(), 5)
        self.assertEqual(transformation_job.records_succeeded, 9950)
        self.assertGreater(entity_mapping.confidence_score, 0.9)
    
    def test_ml_assisted_schema_recognition_workflow(self):
        """Test ML-assisted schema recognition in migration workflow."""
        # Create schema data from entities
        schema_data = [
            {
                'name': self.source_customer_entity.name,
                'fields': [
                    {
                        'name': field.name,
                        'type': field.data_type
                    }
                    for field in self.source_fields
                ]
            }
        ]
        
        # Test schema recognition
        schema_model = AdvancedSchemaRecognitionModel()
        predictions = schema_model.predict_schema_types(schema_data)
        
        self.assertEqual(len(predictions), 1)
        self.assertEqual(predictions[0]['entity_name'], 'legacy_customers')
        self.assertEqual(predictions[0]['predicted_type'], 'person')
        self.assertGreater(predictions[0]['confidence'], 0.5)
    
    def test_data_quality_assessment_workflow(self):
        """Test data quality assessment in migration workflow."""
        # Create sample data with quality issues
        sample_data = pd.DataFrame({
            'cust_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'fname': ['John', 'Jane', None, 'Bob', 'Alice', 'Charlie', 'Diana', 'Eve', 'Frank', 'Grace'],
            'lname': ['Doe', 'Smith', 'Johnson', 'Brown', 'Davis', 'Wilson', 'Moore', 'Taylor', 'Anderson', 'Thomas'],
            'email_addr': [
                'john@example.com', 'jane@example.com', 'invalid-email', 'bob@example.com',
                'alice@example.com', 'charlie@example.com', 'diana@example.com', 'eve@example.com',
                'frank@example.com', 'grace@example.com'
            ]
        })
        
        # Assess data quality
        quality_model = DataQualityAssessmentModel()
        quality_report = quality_model.assess_data_quality(sample_data)
        
        # Verify quality assessment
        self.assertIn('overall_score', quality_report)
        self.assertIn('completeness', quality_report)
        self.assertIn('validity', quality_report)
        self.assertIn('recommendations', quality_report)
        
        # Should detect missing value and invalid email
        self.assertEqual(quality_report['completeness']['missing_cells'], 1)
        self.assertEqual(quality_report['validity']['invalid_emails'], 1)
    
    def test_error_handling_in_workflow(self):
        """Test error handling in migration workflow."""
        project = MigrationProject.objects.create(
            name='Error Test Migration',
            source_system='Source',
            target_system='Target',
            status='DRAFT'
        )
        
        task = MigrationTask.objects.create(
            project=project,
            name='Test Task',
            task_type='ANALYSIS',
            status='PENDING'
        )
        
        # Simulate task failure
        task.status = 'FAILED'
        task.error_message = 'Connection to source database failed'
        task.save()
        
        # Project should remain in progress but track failed tasks
        project.status = 'IN_PROGRESS'
        project.save()
        
        failed_tasks = project.tasks.filter(status='FAILED')
        self.assertEqual(failed_tasks.count(), 1)
        self.assertEqual(failed_tasks.first().error_message, 'Connection to source database failed')


class APIIntegrationWorkflowTests(APITestCase):
    """Test API integration workflows."""
    
    def setUp(self):
        """Set up API test data."""
        self.tenant = Tenant.objects.create(
            name='API Test Tenant',
            slug='api-tenant'
        )
        
        self.user = User.objects.create_user(
            username='apiuser',
            email='api@example.com',
            password='testpass123'
        )
        
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            tenant=self.tenant
        )
        
        self.client.force_authenticate(user=self.user)
    
    def test_create_migration_project_via_api(self):
        """Test creating migration project through API."""
        data = {
            'name': 'API Migration Project',
            'description': 'Project created via API',
            'source_system': 'Legacy System',
            'target_system': 'New System',
            'status': 'DRAFT'
        }
        
        response = self.client.post('/api/orchestrator/projects/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'API Migration Project')
        
        # Verify project was created
        project = MigrationProject.objects.get(id=response.data['id'])
        self.assertEqual(project.name, 'API Migration Project')
    
    def test_create_data_source_and_entities_via_api(self):
        """Test creating data source and entities through API."""
        # Create data source
        ds_data = {
            'name': 'API Test Database',
            'source_type': 'postgresql',
            'connection_string': 'postgresql://user:pass@localhost:5432/test'
        }
        
        ds_response = self.client.post('/api/analyzer/data-sources/', ds_data, format='json')
        self.assertEqual(ds_response.status_code, status.HTTP_201_CREATED)
        
        data_source_id = ds_response.data['id']
        
        # Create entity
        entity_data = {
            'data_source': data_source_id,
            'name': 'api_customers',
            'original_name': 'customers',
            'record_count': 1000,
            'description': 'Customer entity created via API'
        }
        
        entity_response = self.client.post('/api/analyzer/entities/', entity_data, format='json')
        self.assertEqual(entity_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(entity_response.data['name'], 'api_customers')
        
        # Create field
        field_data = {
            'entity': entity_response.data['id'],
            'name': 'customer_id',
            'original_name': 'customer_id',
            'data_type': 'integer',
            'is_primary_key': True,
            'is_nullable': False
        }
        
        field_response = self.client.post('/api/analyzer/fields/', field_data, format='json')
        self.assertEqual(field_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(field_response.data['name'], 'customer_id')
    
    def test_workflow_status_tracking_via_api(self):
        """Test tracking workflow status through API."""
        # Create project
        project_data = {
            'name': 'Status Tracking Project',
            'source_system': 'Source',
            'target_system': 'Target',
            'status': 'DRAFT'
        }
        
        project_response = self.client.post('/api/orchestrator/projects/', project_data, format='json')
        project_id = project_response.data['id']
        
        # Create task
        task_data = {
            'project': project_id,
            'name': 'Test Task',
            'task_type': 'ANALYSIS',
            'status': 'PENDING'
        }
        
        task_response = self.client.post('/api/orchestrator/tasks/', task_data, format='json')
        task_id = task_response.data['id']
        
        # Update task status
        update_data = {
            'project': project_id,
            'name': 'Test Task',
            'task_type': 'ANALYSIS',
            'status': 'IN_PROGRESS'
        }
        
        update_response = self.client.put(f'/api/orchestrator/tasks/{task_id}/', update_data, format='json')
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['status'], 'IN_PROGRESS')
        
        # Check project status
        project_detail = self.client.get(f'/api/orchestrator/projects/{project_id}/')
        self.assertEqual(project_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(len(project_detail.data['tasks']), 1)
        self.assertEqual(project_detail.data['tasks'][0]['status'], 'IN_PROGRESS')


@pytest.mark.django_db
class PerformanceIntegrationTests:
    """Performance tests for integration workflows."""
    
    def test_large_dataset_migration_workflow(self):
        """Test migration workflow with large datasets."""
        # Create tenant and user
        tenant = Tenant.objects.create(name='Perf Tenant', slug='perf-tenant')
        user = User.objects.create_user(username='perfuser', email='perf@example.com', password='pass')
        
        # Create data source with many entities
        data_source = DataSource.objects.create(
            name='Large Database',
            source_type='postgresql'
        )
        
        # Create multiple entities
        entities = []
        for i in range(10):
            entity = Entity.objects.create(
                data_source=data_source,
                name=f'table_{i}',
                original_name=f'table_{i}',
                record_count=100000
            )
            entities.append(entity)
            
            # Create fields for each entity
            for j in range(20):
                Field.objects.create(
                    entity=entity,
                    name=f'field_{j}',
                    original_name=f'field_{j}',
                    data_type='string'
                )
        
        # Test that we can handle large numbers of entities and fields
        assert Entity.objects.count() == 10
        assert Field.objects.count() == 200
        
        # Test schema recognition performance
        schema_data = []
        for entity in entities:
            schema_data.append({
                'name': entity.name,
                'fields': [
                    {'name': field.name, 'type': field.data_type}
                    for field in entity.fields.all()
                ]
            })
        
        model = AdvancedSchemaRecognitionModel()
        
        import time
        start_time = time.time()
        predictions = model.predict_schema_types(schema_data)
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 10.0  # 10 seconds max
        assert len(predictions) == 10
