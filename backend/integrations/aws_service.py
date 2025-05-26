"""
AWS integration service for MigrateIQ.
"""

import boto3
import pandas as pd
from botocore.exceptions import ClientError, NoCredentialsError
from django.conf import settings
from django.utils import timezone
from typing import Dict, List, Any, Optional
import logging
import json
from .base_service import BaseCloudService

logger = logging.getLogger(__name__)


class AWSService(BaseCloudService):
    """Service for AWS integrations."""
    
    def __init__(self, provider_config: Dict[str, Any]):
        """Initialize AWS service with provider configuration."""
        super().__init__(provider_config)
        self.provider_type = 'aws'
        self.region = provider_config.get('region', 'us-east-1')
        self.access_key = provider_config.get('access_key')
        self.secret_key = provider_config.get('secret_key')
        self.session_token = provider_config.get('session_token')
        
        # Initialize AWS session
        self.session = self._create_session()
        
    def _create_session(self) -> boto3.Session:
        """Create AWS session with credentials."""
        try:
            session = boto3.Session(
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                aws_session_token=self.session_token,
                region_name=self.region
            )
            return session
        except Exception as e:
            logger.error(f"Failed to create AWS session: {str(e)}")
            raise
    
    def test_connection(self) -> Dict[str, Any]:
        """Test AWS connection."""
        try:
            # Test with STS to verify credentials
            sts = self.session.client('sts')
            identity = sts.get_caller_identity()
            
            return {
                'success': True,
                'message': 'AWS connection successful',
                'account_id': identity.get('Account'),
                'user_id': identity.get('UserId'),
                'arn': identity.get('Arn')
            }
        except NoCredentialsError:
            return {
                'success': False,
                'message': 'AWS credentials not found or invalid'
            }
        except ClientError as e:
            return {
                'success': False,
                'message': f"AWS connection failed: {e.response['Error']['Message']}"
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Unexpected error: {str(e)}"
            }
    
    def list_s3_buckets(self) -> List[Dict[str, Any]]:
        """List all S3 buckets."""
        try:
            s3 = self.session.client('s3')
            response = s3.list_buckets()
            
            buckets = []
            for bucket in response.get('Buckets', []):
                bucket_info = {
                    'name': bucket['Name'],
                    'creation_date': bucket['CreationDate'].isoformat(),
                    'region': self._get_bucket_region(bucket['Name'])
                }
                buckets.append(bucket_info)
            
            return buckets
        except Exception as e:
            logger.error(f"Failed to list S3 buckets: {str(e)}")
            return []
    
    def _get_bucket_region(self, bucket_name: str) -> str:
        """Get the region of an S3 bucket."""
        try:
            s3 = self.session.client('s3')
            response = s3.get_bucket_location(Bucket=bucket_name)
            region = response.get('LocationConstraint')
            return region if region else 'us-east-1'
        except Exception:
            return 'unknown'
    
    def list_s3_objects(self, bucket_name: str, prefix: str = '') -> List[Dict[str, Any]]:
        """List objects in an S3 bucket."""
        try:
            s3 = self.session.client('s3')
            paginator = s3.get_paginator('list_objects_v2')
            
            objects = []
            for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
                for obj in page.get('Contents', []):
                    object_info = {
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'etag': obj['ETag'].strip('"'),
                        'storage_class': obj.get('StorageClass', 'STANDARD')
                    }
                    objects.append(object_info)
            
            return objects
        except Exception as e:
            logger.error(f"Failed to list S3 objects: {str(e)}")
            return []
    
    def read_s3_file(self, bucket_name: str, key: str, file_format: str = 'csv') -> pd.DataFrame:
        """Read a file from S3 into a pandas DataFrame."""
        try:
            s3 = self.session.client('s3')
            obj = s3.get_object(Bucket=bucket_name, Key=key)
            
            if file_format.lower() == 'csv':
                return pd.read_csv(obj['Body'])
            elif file_format.lower() == 'json':
                return pd.read_json(obj['Body'])
            elif file_format.lower() == 'parquet':
                return pd.read_parquet(obj['Body'])
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
                
        except Exception as e:
            logger.error(f"Failed to read S3 file: {str(e)}")
            raise
    
    def write_s3_file(self, df: pd.DataFrame, bucket_name: str, key: str, file_format: str = 'csv') -> bool:
        """Write a pandas DataFrame to S3."""
        try:
            s3 = self.session.client('s3')
            
            if file_format.lower() == 'csv':
                csv_buffer = df.to_csv(index=False)
                s3.put_object(Bucket=bucket_name, Key=key, Body=csv_buffer)
            elif file_format.lower() == 'json':
                json_buffer = df.to_json(orient='records')
                s3.put_object(Bucket=bucket_name, Key=key, Body=json_buffer)
            elif file_format.lower() == 'parquet':
                parquet_buffer = df.to_parquet(index=False)
                s3.put_object(Bucket=bucket_name, Key=key, Body=parquet_buffer)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to write S3 file: {str(e)}")
            return False
    
    def list_rds_instances(self) -> List[Dict[str, Any]]:
        """List RDS instances."""
        try:
            rds = self.session.client('rds')
            response = rds.describe_db_instances()
            
            instances = []
            for instance in response.get('DBInstances', []):
                instance_info = {
                    'identifier': instance['DBInstanceIdentifier'],
                    'engine': instance['Engine'],
                    'engine_version': instance['EngineVersion'],
                    'instance_class': instance['DBInstanceClass'],
                    'status': instance['DBInstanceStatus'],
                    'endpoint': instance.get('Endpoint', {}).get('Address'),
                    'port': instance.get('Endpoint', {}).get('Port'),
                    'allocated_storage': instance.get('AllocatedStorage'),
                    'availability_zone': instance.get('AvailabilityZone')
                }
                instances.append(instance_info)
            
            return instances
        except Exception as e:
            logger.error(f"Failed to list RDS instances: {str(e)}")
            return []
    
    def connect_to_rds(self, instance_identifier: str, database: str, username: str, password: str):
        """Connect to an RDS instance."""
        try:
            rds = self.session.client('rds')
            instance = rds.describe_db_instances(DBInstanceIdentifier=instance_identifier)
            
            endpoint = instance['DBInstances'][0]['Endpoint']['Address']
            port = instance['DBInstances'][0]['Endpoint']['Port']
            engine = instance['DBInstances'][0]['Engine']
            
            # Create connection string based on engine
            if engine.startswith('postgres'):
                connection_string = f"postgresql://{username}:{password}@{endpoint}:{port}/{database}"
            elif engine.startswith('mysql'):
                connection_string = f"mysql://{username}:{password}@{endpoint}:{port}/{database}"
            elif engine.startswith('oracle'):
                connection_string = f"oracle://{username}:{password}@{endpoint}:{port}/{database}"
            else:
                raise ValueError(f"Unsupported RDS engine: {engine}")
            
            return connection_string
        except Exception as e:
            logger.error(f"Failed to connect to RDS: {str(e)}")
            raise
    
    def list_redshift_clusters(self) -> List[Dict[str, Any]]:
        """List Redshift clusters."""
        try:
            redshift = self.session.client('redshift')
            response = redshift.describe_clusters()
            
            clusters = []
            for cluster in response.get('Clusters', []):
                cluster_info = {
                    'identifier': cluster['ClusterIdentifier'],
                    'node_type': cluster['NodeType'],
                    'cluster_status': cluster['ClusterStatus'],
                    'endpoint': cluster.get('Endpoint', {}).get('Address'),
                    'port': cluster.get('Endpoint', {}).get('Port'),
                    'database_name': cluster.get('DBName'),
                    'availability_zone': cluster.get('AvailabilityZone'),
                    'number_of_nodes': cluster.get('NumberOfNodes')
                }
                clusters.append(cluster_info)
            
            return clusters
        except Exception as e:
            logger.error(f"Failed to list Redshift clusters: {str(e)}")
            return []
    
    def list_dynamodb_tables(self) -> List[Dict[str, Any]]:
        """List DynamoDB tables."""
        try:
            dynamodb = self.session.client('dynamodb')
            response = dynamodb.list_tables()
            
            tables = []
            for table_name in response.get('TableNames', []):
                table_info = dynamodb.describe_table(TableName=table_name)
                table_data = {
                    'name': table_name,
                    'status': table_info['Table']['TableStatus'],
                    'item_count': table_info['Table'].get('ItemCount', 0),
                    'table_size_bytes': table_info['Table'].get('TableSizeBytes', 0),
                    'creation_date': table_info['Table']['CreationDateTime'].isoformat()
                }
                tables.append(table_data)
            
            return tables
        except Exception as e:
            logger.error(f"Failed to list DynamoDB tables: {str(e)}")
            return []
    
    def scan_dynamodb_table(self, table_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Scan DynamoDB table and return items."""
        try:
            dynamodb = self.session.resource('dynamodb')
            table = dynamodb.Table(table_name)
            
            response = table.scan(Limit=limit)
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Failed to scan DynamoDB table: {str(e)}")
            return []
    
    def get_service_quotas(self) -> Dict[str, Any]:
        """Get AWS service quotas and usage."""
        try:
            quotas = {}
            
            # S3 quotas
            s3 = self.session.client('s3')
            buckets = s3.list_buckets()
            quotas['s3'] = {
                'bucket_count': len(buckets.get('Buckets', [])),
                'bucket_limit': 100  # Default S3 bucket limit
            }
            
            # RDS quotas
            rds = self.session.client('rds')
            instances = rds.describe_db_instances()
            quotas['rds'] = {
                'instance_count': len(instances.get('DBInstances', [])),
                'instance_limit': 40  # Default RDS instance limit
            }
            
            return quotas
        except Exception as e:
            logger.error(f"Failed to get service quotas: {str(e)}")
            return {}
    
    def estimate_costs(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Estimate costs for AWS operations."""
        # This is a simplified cost estimation
        # In production, you would integrate with AWS Cost Explorer API
        
        cost_estimates = {
            's3_storage': {
                'standard': 0.023,  # per GB per month
                'ia': 0.0125,
                'glacier': 0.004
            },
            'rds_instance': {
                'db.t3.micro': 0.017,  # per hour
                'db.t3.small': 0.034,
                'db.t3.medium': 0.068
            },
            'data_transfer': 0.09  # per GB
        }
        
        return {
            'operation': operation,
            'estimated_cost': 0.0,  # Calculate based on operation
            'currency': 'USD',
            'period': 'monthly',
            'details': cost_estimates.get(operation, {})
        }
