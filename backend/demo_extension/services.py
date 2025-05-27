import requests
import time
from typing import Dict, List, Optional
from django.utils import timezone
from django.db import transaction
from .models import CustomDataConnector, SyncLog

class DataSyncService:
    """Service for synchronizing data from external APIs."""
    
    def __init__(self, connector: CustomDataConnector):
        self.connector = connector
    
    def test_connection(self) -> bool:
        """Test connection to the API endpoint."""
        try:
            headers = self._get_headers()
            response = requests.get(
                self.connector.api_endpoint,
                headers=headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False
    
    @transaction.atomic
    def sync_data(self) -> SyncLog:
        """Synchronize data from the API endpoint."""
        start_time = time.time()
        
        # Create sync log
        sync_log = SyncLog.objects.create(
            connector=self.connector,
            status='PARTIAL'  # Will update based on result
        )
        
        try:
            # Fetch data from API
            data = self._fetch_data()
            
            # Process the data
            processed_count = self._process_data(data)
            
            # Update sync log with success
            duration = time.time() - start_time
            sync_log.status = 'SUCCESS'
            sync_log.records_processed = processed_count
            sync_log.duration_seconds = duration
            sync_log.save()
            
            # Update connector stats
            self.connector.last_sync = timezone.now()
            self.connector.records_synced += processed_count
            self.connector.save()
            
        except Exception as e:
            # Update sync log with failure
            duration = time.time() - start_time
            sync_log.status = 'FAILED'
            sync_log.error_message = str(e)
            sync_log.duration_seconds = duration
            sync_log.save()
            raise
        
        return sync_log
    
    def _fetch_data(self) -> List[Dict]:
        """Fetch data from the API endpoint."""
        headers = self._get_headers()
        
        # For demo purposes, we'll create some sample data
        # In a real implementation, you would make the actual API call
        if 'jsonplaceholder' in self.connector.api_endpoint:
            # Use JSONPlaceholder for demo
            response = requests.get(
                self.connector.api_endpoint,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        else:
            # Return sample data for demo
            return [
                {'id': 1, 'name': 'Sample Record 1', 'value': 100},
                {'id': 2, 'name': 'Sample Record 2', 'value': 200},
                {'id': 3, 'name': 'Sample Record 3', 'value': 300},
            ]
    
    def _process_data(self, data: List[Dict]) -> int:
        """Process the fetched data."""
        processed_count = 0
        
        for record in data:
            # In a real implementation, you would:
            # 1. Validate the record
            # 2. Transform the data if needed
            # 3. Save to your database
            # 4. Handle any errors
            
            # For demo, we'll just count the records
            if self._validate_record(record):
                processed_count += 1
        
        return processed_count
    
    def _validate_record(self, record: Dict) -> bool:
        """Validate a single record."""
        # Basic validation - ensure record has required fields
        required_fields = ['id']
        return all(field in record for field in required_fields)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests."""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'MigrateIQ-Demo/1.0'
        }
        
        if self.connector.api_key:
            headers['Authorization'] = f'Bearer {self.connector.api_key}'
        
        return headers

class ConnectorStatsService:
    """Service for generating connector statistics."""
    
    @staticmethod
    def get_stats(tenant=None) -> Dict:
        """Get connector statistics for a tenant."""
        from django.db.models import Count, Sum, Avg
        from datetime import datetime, timedelta
        
        # Filter by tenant if provided
        connectors = CustomDataConnector.objects.all()
        if tenant:
            connectors = connectors.filter(tenant=tenant)
        
        # Basic stats
        total_connectors = connectors.count()
        active_connectors = connectors.filter(is_active=True).count()
        total_records_synced = connectors.aggregate(
            total=Sum('records_synced')
        )['total'] or 0
        
        # Recent sync stats
        last_24h = timezone.now() - timedelta(hours=24)
        recent_syncs = SyncLog.objects.filter(
            connector__in=connectors,
            created_at__gte=last_24h
        )
        
        last_24h_syncs = recent_syncs.count()
        successful_syncs = recent_syncs.filter(status='SUCCESS').count()
        success_rate = (successful_syncs / last_24h_syncs * 100) if last_24h_syncs > 0 else 0
        
        avg_duration = recent_syncs.aggregate(
            avg=Avg('duration_seconds')
        )['avg'] or 0
        
        return {
            'total_connectors': total_connectors,
            'active_connectors': active_connectors,
            'total_records_synced': total_records_synced,
            'last_24h_syncs': last_24h_syncs,
            'success_rate': round(success_rate, 2),
            'avg_sync_duration': round(avg_duration, 2)
        }

class DataTransformationService:
    """Service for transforming data during sync."""
    
    def __init__(self, transformation_rules: Dict):
        self.rules = transformation_rules
    
    def transform_record(self, record: Dict) -> Dict:
        """Transform a single record based on rules."""
        transformed = record.copy()
        
        # Apply field mappings
        if 'field_mappings' in self.rules:
            for old_field, new_field in self.rules['field_mappings'].items():
                if old_field in transformed:
                    transformed[new_field] = transformed.pop(old_field)
        
        # Apply data type conversions
        if 'type_conversions' in self.rules:
            for field, target_type in self.rules['type_conversions'].items():
                if field in transformed:
                    transformed[field] = self._convert_type(
                        transformed[field], target_type
                    )
        
        # Apply custom transformations
        if 'custom_transforms' in self.rules:
            for field, transform_func in self.rules['custom_transforms'].items():
                if field in transformed:
                    transformed[field] = transform_func(transformed[field])
        
        return transformed
    
    def _convert_type(self, value, target_type: str):
        """Convert value to target type."""
        try:
            if target_type == 'int':
                return int(value)
            elif target_type == 'float':
                return float(value)
            elif target_type == 'str':
                return str(value)
            elif target_type == 'bool':
                return bool(value)
            else:
                return value
        except (ValueError, TypeError):
            return value  # Return original value if conversion fails
