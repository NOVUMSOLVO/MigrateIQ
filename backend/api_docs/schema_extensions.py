"""
Custom schema extensions for API documentation.
"""

from drf_spectacular.extensions import OpenApiViewExtension, OpenApiSerializerExtension
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.openapi import AutoSchema
from rest_framework import status
from typing import Dict, Any, List


class MigrateIQAutoSchema(AutoSchema):
    """Custom auto schema for MigrateIQ API documentation."""
    
    def get_operation_id(self):
        """Generate operation ID for API endpoints."""
        operation_id = super().get_operation_id()
        
        # Add version prefix if available
        if hasattr(self.view, 'versioning_class'):
            version = getattr(self.request, 'version', 'v1')
            operation_id = f"{version}_{operation_id}"
        
        return operation_id
    
    def get_tags(self):
        """Get tags for API endpoints."""
        tags = super().get_tags()
        
        # Add custom tags based on app name
        if hasattr(self.view, 'get_queryset'):
            model = getattr(self.view.get_queryset(), 'model', None)
            if model:
                app_label = model._meta.app_label
                tags.append(app_label.title())
        
        return tags


class TenantParameterExtension(OpenApiViewExtension):
    """Add tenant parameter to multi-tenant endpoints."""
    
    target_component = 'migrateiq.views'
    
    def view_replacement(self):
        """Add tenant parameter to view schema."""
        if hasattr(self.target, 'tenant_required') and self.target.tenant_required:
            return extend_schema(
                parameters=[
                    OpenApiParameter(
                        name='X-Tenant-ID',
                        type=str,
                        location=OpenApiParameter.HEADER,
                        description='Tenant identifier for multi-tenant operations',
                        required=True
                    )
                ]
            )(self.target)
        return self.target


class PaginationExtension(OpenApiViewExtension):
    """Add pagination parameters to list endpoints."""
    
    target_component = 'rest_framework.generics.ListAPIView'
    
    def view_replacement(self):
        """Add pagination parameters."""
        return extend_schema(
            parameters=[
                OpenApiParameter(
                    name='page',
                    type=int,
                    location=OpenApiParameter.QUERY,
                    description='Page number for pagination'
                ),
                OpenApiParameter(
                    name='page_size',
                    type=int,
                    location=OpenApiParameter.QUERY,
                    description='Number of items per page'
                ),
                OpenApiParameter(
                    name='cursor',
                    type=str,
                    location=OpenApiParameter.QUERY,
                    description='Cursor for cursor-based pagination'
                )
            ]
        )(self.target)


class FilteringExtension(OpenApiViewExtension):
    """Add filtering parameters to filterable endpoints."""
    
    target_component = 'django_filters.rest_framework.DjangoFilterBackend'
    
    def view_replacement(self):
        """Add filtering parameters."""
        filter_params = []
        
        if hasattr(self.target, 'filterset_fields'):
            for field in self.target.filterset_fields:
                filter_params.append(
                    OpenApiParameter(
                        name=field,
                        type=str,
                        location=OpenApiParameter.QUERY,
                        description=f'Filter by {field}'
                    )
                )
        
        return extend_schema(parameters=filter_params)(self.target)


# Common response schemas
COMMON_RESPONSES = {
    400: {
        'description': 'Bad Request',
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'error': {'type': 'string'},
                        'details': {'type': 'object'},
                        'code': {'type': 'string'}
                    }
                }
            }
        }
    },
    401: {
        'description': 'Unauthorized',
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'error': {'type': 'string', 'example': 'Authentication required'}
                    }
                }
            }
        }
    },
    403: {
        'description': 'Forbidden',
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'error': {'type': 'string', 'example': 'Permission denied'}
                    }
                }
            }
        }
    },
    404: {
        'description': 'Not Found',
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'error': {'type': 'string', 'example': 'Resource not found'}
                    }
                }
            }
        }
    },
    429: {
        'description': 'Too Many Requests',
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'error': {'type': 'string', 'example': 'Rate limit exceeded'},
                        'retry_after': {'type': 'integer', 'example': 60}
                    }
                }
            }
        }
    },
    500: {
        'description': 'Internal Server Error',
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'error': {'type': 'string', 'example': 'Internal server error'},
                        'request_id': {'type': 'string'}
                    }
                }
            }
        }
    }
}


# Common examples
COMMON_EXAMPLES = {
    'project_create': OpenApiExample(
        'Create Project',
        summary='Create a new migration project',
        description='Example of creating a new data migration project',
        value={
            'name': 'Customer Data Migration',
            'description': 'Migrate customer data from legacy system',
            'source_system': 1,
            'target_system': 2,
            'migration_type': 'full',
            'schedule': {
                'start_date': '2024-01-15T10:00:00Z',
                'frequency': 'once'
            }
        }
    ),
    'data_source_create': OpenApiExample(
        'Create Data Source',
        summary='Create a new data source',
        description='Example of creating a new data source connection',
        value={
            'name': 'Production Database',
            'type': 'postgresql',
            'connection_string': 'postgresql://user:pass@host:5432/db',
            'schema_name': 'public',
            'is_active': True
        }
    ),
    'migration_status': OpenApiExample(
        'Migration Status',
        summary='Migration progress status',
        description='Example of migration progress response',
        value={
            'status': 'running',
            'progress': 65,
            'total_records': 100000,
            'processed_records': 65000,
            'failed_records': 150,
            'estimated_completion': '2024-01-15T14:30:00Z',
            'current_phase': 'data_transformation'
        }
    )
}


def get_standard_responses(additional_responses: Dict[int, Dict] = None) -> Dict[int, Dict]:
    """Get standard API responses with optional additional responses."""
    responses = COMMON_RESPONSES.copy()
    
    if additional_responses:
        responses.update(additional_responses)
    
    return responses


def get_success_response(description: str, schema: Dict = None) -> Dict[int, Dict]:
    """Get success response schema."""
    response_schema = schema or {
        'type': 'object',
        'properties': {
            'success': {'type': 'boolean', 'example': True},
            'message': {'type': 'string'}
        }
    }
    
    return {
        200: {
            'description': description,
            'content': {
                'application/json': {
                    'schema': response_schema
                }
            }
        }
    }


def get_list_response(item_schema: Dict, description: str = None) -> Dict[int, Dict]:
    """Get paginated list response schema."""
    return {
        200: {
            'description': description or 'List of items',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'count': {'type': 'integer'},
                            'next': {'type': 'string', 'nullable': True},
                            'previous': {'type': 'string', 'nullable': True},
                            'results': {
                                'type': 'array',
                                'items': item_schema
                            }
                        }
                    }
                }
            }
        }
    }


def get_create_response(item_schema: Dict, description: str = None) -> Dict[int, Dict]:
    """Get create response schema."""
    return {
        201: {
            'description': description or 'Item created successfully',
            'content': {
                'application/json': {
                    'schema': item_schema
                }
            }
        }
    }


# Custom serializer extensions
class TimestampSerializerExtension(OpenApiSerializerExtension):
    """Add timestamp field descriptions."""
    
    target_component = 'rest_framework.serializers.DateTimeField'
    
    def map_serializer_field(self, auto_schema, direction):
        """Map datetime field with enhanced description."""
        schema = super().map_serializer_field(auto_schema, direction)
        
        field_name = getattr(self.target, 'source', None) or getattr(self.target, 'field_name', '')
        
        if 'created' in field_name.lower():
            schema['description'] = 'Timestamp when the resource was created (ISO 8601 format)'
        elif 'updated' in field_name.lower() or 'modified' in field_name.lower():
            schema['description'] = 'Timestamp when the resource was last updated (ISO 8601 format)'
        elif 'deleted' in field_name.lower():
            schema['description'] = 'Timestamp when the resource was deleted (ISO 8601 format)'
        
        schema['example'] = '2024-01-15T10:30:00Z'
        
        return schema


class UUIDSerializerExtension(OpenApiSerializerExtension):
    """Add UUID field descriptions."""
    
    target_component = 'rest_framework.serializers.UUIDField'
    
    def map_serializer_field(self, auto_schema, direction):
        """Map UUID field with enhanced description."""
        schema = super().map_serializer_field(auto_schema, direction)
        
        schema['description'] = 'Unique identifier (UUID4 format)'
        schema['example'] = '123e4567-e89b-12d3-a456-426614174000'
        schema['pattern'] = '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
        
        return schema
