"""
Base service class for cloud integrations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseCloudService(ABC):
    """Abstract base class for cloud service integrations."""
    
    def __init__(self, provider_config: Dict[str, Any]):
        """Initialize the cloud service with provider configuration."""
        self.provider_config = provider_config
        self.provider_type = None
        
    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Test the connection to the cloud provider."""
        pass
    
    @abstractmethod
    def list_data_sources(self) -> List[Dict[str, Any]]:
        """List available data sources."""
        pass
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the cloud provider."""
        return {
            'provider_type': self.provider_type,
            'config': self.provider_config
        }
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate the provider configuration."""
        required_fields = self.get_required_config_fields()
        missing_fields = []
        
        for field in required_fields:
            if field not in self.provider_config or not self.provider_config[field]:
                missing_fields.append(field)
        
        if missing_fields:
            return {
                'valid': False,
                'message': f"Missing required fields: {', '.join(missing_fields)}"
            }
        
        return {'valid': True, 'message': 'Configuration is valid'}
    
    def get_required_config_fields(self) -> List[str]:
        """Get list of required configuration fields."""
        return []
    
    def get_optional_config_fields(self) -> List[str]:
        """Get list of optional configuration fields."""
        return []
    
    def get_supported_data_types(self) -> List[str]:
        """Get list of supported data types."""
        return []
    
    def get_supported_operations(self) -> List[str]:
        """Get list of supported operations."""
        return ['read', 'write', 'list', 'test']
    
    def format_error(self, error: Exception) -> Dict[str, Any]:
        """Format error for consistent error handling."""
        return {
            'error': True,
            'error_type': type(error).__name__,
            'message': str(error),
            'provider': self.provider_type
        }
    
    def log_operation(self, operation: str, success: bool, details: Dict[str, Any] = None):
        """Log cloud operation for auditing."""
        log_data = {
            'provider': self.provider_type,
            'operation': operation,
            'success': success,
            'details': details or {}
        }
        
        if success:
            logger.info(f"Cloud operation successful: {log_data}")
        else:
            logger.error(f"Cloud operation failed: {log_data}")


class CloudServiceFactory:
    """Factory class for creating cloud service instances."""
    
    _services = {}
    
    @classmethod
    def register_service(cls, provider_type: str, service_class):
        """Register a cloud service class."""
        cls._services[provider_type] = service_class
    
    @classmethod
    def create_service(cls, provider_type: str, provider_config: Dict[str, Any]) -> BaseCloudService:
        """Create a cloud service instance."""
        if provider_type not in cls._services:
            raise ValueError(f"Unsupported provider type: {provider_type}")
        
        service_class = cls._services[provider_type]
        return service_class(provider_config)
    
    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """Get list of supported cloud providers."""
        return list(cls._services.keys())


# Register services when module is imported
def register_default_services():
    """Register default cloud services."""
    try:
        from .aws_service import AWSService
        CloudServiceFactory.register_service('aws', AWSService)
    except ImportError:
        logger.warning("AWS service not available")
    
    try:
        from .azure_service import AzureService
        CloudServiceFactory.register_service('azure', AzureService)
    except ImportError:
        logger.warning("Azure service not available")
    
    try:
        from .gcp_service import GCPService
        CloudServiceFactory.register_service('gcp', GCPService)
    except ImportError:
        logger.warning("GCP service not available")


# Auto-register services
register_default_services()
