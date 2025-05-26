"""
Simple URL configuration for MigrateIQ development.
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.decorators import api_view
from rest_framework.response import Response

def api_root(request):
    """Simple API root view."""
    return JsonResponse({
        'message': 'Welcome to MigrateIQ API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'admin': '/admin/',
            'api_docs': '/api/docs/',
            'api_schema': '/api/schema/',
            'api_redoc': '/api/redoc/',
        }
    })

def health_check(request):
    """Simple health check endpoint."""
    return JsonResponse({
        'status': 'healthy',
        'service': 'MigrateIQ',
        'version': '1.0.0'
    })

@api_view(['GET'])
def analyzer_status(request):
    """Simple analyzer status endpoint."""
    return Response({
        'module': 'analyzer',
        'status': 'active',
        'description': 'Data source analysis and schema discovery',
        'endpoints': [
            '/api/analyzer/status/',
            '/api/analyzer/sources/',
            '/api/analyzer/entities/'
        ]
    })

@api_view(['GET'])
def orchestrator_status(request):
    """Simple orchestrator status endpoint."""
    return Response({
        'module': 'orchestrator',
        'status': 'active',
        'description': 'Migration workflow orchestration and task management',
        'endpoints': [
            '/api/orchestrator/status/',
            '/api/orchestrator/projects/',
            '/api/orchestrator/tasks/'
        ]
    })

@api_view(['GET'])
def modules_status(request):
    """Show status of all available modules."""
    return Response({
        'service': 'MigrateIQ',
        'version': '1.0.0',
        'modules': {
            'core': {
                'status': 'active',
                'description': 'Core system functionality and tenant management',
                'features': ['Multi-tenancy', 'User management', 'Audit logging']
            },
            'authentication': {
                'status': 'active',
                'description': 'User authentication and authorization',
                'features': ['JWT tokens', 'Role-based access', 'Session management']
            },
            'analyzer': {
                'status': 'active',
                'description': 'Data source analysis and schema discovery',
                'features': ['Schema detection', 'Data profiling', 'Source connectivity']
            },
            'orchestrator': {
                'status': 'active',
                'description': 'Migration workflow orchestration and task management',
                'features': ['Workflow management', 'Task scheduling', 'Progress tracking']
            },
            'validation': {
                'status': 'active',
                'description': 'Data validation and quality assurance',
                'features': ['Data quality checks', 'Validation rules', 'Error reporting']
            },
            'transformation': {
                'status': 'active',
                'description': 'Data transformation and mapping',
                'features': ['Field mapping', 'Data transformation', 'Format conversion']
            },
            'mapping_engine': {
                'status': 'active',
                'description': 'Schema and field mapping management',
                'features': ['Schema mapping', 'Field relationships', 'Mapping validation']
            },
            'ml': {
                'status': 'active',
                'description': 'Machine learning and AI-powered features',
                'features': ['Schema recognition', 'Data quality assessment', 'Smart mapping']
            }
        },
        'available_endpoints': [
            '/api/modules/',
            '/api/analyzer/status/',
            '/api/orchestrator/status/',
            '/api/validation/status/',
            '/api/transformation/status/',
            '/api/mapping/status/',
            '/api/ml/status/',
            '/api/projects/',
            '/api/datasources/',
            '/health/',
            '/admin/'
        ]
    })

@api_view(['GET'])
def validation_status(request):
    """Validation module status endpoint."""
    return Response({
        'module': 'validation',
        'status': 'active',
        'description': 'Data validation and quality assurance',
        'features': ['Data quality checks', 'Validation rules', 'Error reporting'],
        'endpoints': ['/api/validation/status/', '/api/validation/rules/', '/api/validation/results/']
    })

@api_view(['GET'])
def transformation_status(request):
    """Transformation module status endpoint."""
    return Response({
        'module': 'transformation',
        'status': 'active',
        'description': 'Data transformation and mapping',
        'features': ['Field mapping', 'Data transformation', 'Format conversion'],
        'endpoints': ['/api/transformation/status/', '/api/transformation/jobs/', '/api/transformation/rules/']
    })

@api_view(['GET'])
def mapping_status(request):
    """Mapping engine status endpoint."""
    return Response({
        'module': 'mapping_engine',
        'status': 'active',
        'description': 'Schema and field mapping management',
        'features': ['Schema mapping', 'Field relationships', 'Mapping validation'],
        'endpoints': ['/api/mapping/status/', '/api/mapping/schemas/', '/api/mapping/fields/']
    })

@api_view(['GET'])
def ml_status(request):
    """ML module status endpoint."""
    return Response({
        'module': 'ml',
        'status': 'active',
        'description': 'Machine learning and AI-powered features',
        'features': ['Schema recognition', 'Data quality assessment', 'Smart mapping'],
        'endpoints': ['/api/ml/status/', '/api/ml/models/', '/api/ml/predictions/']
    })

@api_view(['GET', 'POST'])
def projects_api(request):
    """Migration projects API endpoint."""
    if request.method == 'GET':
        return Response({
            'projects': [
                {
                    'id': 1,
                    'name': 'Customer Data Migration',
                    'status': 'in_progress',
                    'source': 'MySQL Database',
                    'target': 'PostgreSQL Database',
                    'progress': 75,
                    'created_at': '2024-05-26T10:00:00Z'
                },
                {
                    'id': 2,
                    'name': 'Legacy System Migration',
                    'status': 'completed',
                    'source': 'Oracle Database',
                    'target': 'MongoDB',
                    'progress': 100,
                    'created_at': '2024-05-25T14:30:00Z'
                }
            ],
            'total': 2,
            'page': 1,
            'per_page': 10
        })
    else:  # POST
        return Response({
            'message': 'Project creation endpoint',
            'status': 'success',
            'project_id': 3
        }, status=201)

@api_view(['GET', 'POST'])
def datasources_api(request):
    """Data sources API endpoint."""
    if request.method == 'GET':
        return Response({
            'datasources': [
                {
                    'id': 1,
                    'name': 'Production MySQL',
                    'type': 'mysql',
                    'host': 'prod-mysql.company.com',
                    'status': 'connected',
                    'last_tested': '2024-05-26T09:30:00Z'
                },
                {
                    'id': 2,
                    'name': 'Analytics PostgreSQL',
                    'type': 'postgresql',
                    'host': 'analytics-pg.company.com',
                    'status': 'connected',
                    'last_tested': '2024-05-26T09:25:00Z'
                },
                {
                    'id': 3,
                    'name': 'Legacy Oracle',
                    'type': 'oracle',
                    'host': 'legacy-oracle.company.com',
                    'status': 'disconnected',
                    'last_tested': '2024-05-25T16:00:00Z'
                }
            ],
            'total': 3,
            'page': 1,
            'per_page': 10
        })
    else:  # POST
        return Response({
            'message': 'Data source creation endpoint',
            'status': 'success',
            'datasource_id': 4
        }, status=201)

@api_view(['POST'])
def auth_login(request):
    """Authentication login endpoint."""
    return Response({
        'message': 'Login successful',
        'token': 'jwt-token-example-12345',
        'user': {
            'id': 1,
            'username': 'admin',
            'email': 'admin@migrateiq.com',
            'role': 'administrator'
        }
    })

@api_view(['POST'])
def auth_logout(request):
    """Authentication logout endpoint."""
    return Response({
        'message': 'Logout successful'
    })

@api_view(['GET'])
def auth_profile(request):
    """User profile endpoint."""
    return Response({
        'user': {
            'id': 1,
            'username': 'admin',
            'email': 'admin@migrateiq.com',
            'role': 'administrator',
            'last_login': '2024-05-26T10:30:00Z',
            'permissions': [
                'create_projects',
                'manage_datasources',
                'view_analytics',
                'admin_access'
            ]
        }
    })

@api_view(['GET'])
def analytics_dashboard(request):
    """Analytics dashboard endpoint."""
    return Response({
        'dashboard': {
            'total_projects': 15,
            'active_migrations': 3,
            'completed_migrations': 12,
            'total_data_sources': 8,
            'success_rate': 94.5,
            'avg_migration_time': '2.3 hours',
            'recent_activity': [
                {
                    'type': 'migration_completed',
                    'project': 'Customer Data Migration',
                    'timestamp': '2024-05-26T09:45:00Z'
                },
                {
                    'type': 'datasource_added',
                    'name': 'Analytics PostgreSQL',
                    'timestamp': '2024-05-26T08:30:00Z'
                },
                {
                    'type': 'migration_started',
                    'project': 'Legacy System Migration',
                    'timestamp': '2024-05-26T07:15:00Z'
                }
            ]
        }
    })

@api_view(['GET'])
def system_metrics(request):
    """System metrics endpoint."""
    return Response({
        'metrics': {
            'cpu_usage': 45.2,
            'memory_usage': 62.8,
            'disk_usage': 34.1,
            'network_io': {
                'bytes_sent': 1024000,
                'bytes_received': 2048000
            },
            'database': {
                'connections': 12,
                'queries_per_second': 45,
                'avg_response_time': '15ms'
            },
            'uptime': '5 days, 12 hours',
            'last_backup': '2024-05-26T02:00:00Z'
        }
    })

@api_view(['GET'])
def realtime_analytics(request):
    """Real-time analytics endpoint."""
    import random
    import time

    return Response({
        'timestamp': int(time.time()),
        'realtime_metrics': {
            'active_connections': random.randint(50, 200),
            'current_cpu': round(random.uniform(20, 80), 1),
            'current_memory': round(random.uniform(40, 90), 1),
            'migrations_in_progress': random.randint(1, 5),
            'data_transfer_rate': f"{random.randint(10, 100)} MB/s",
            'queue_size': random.randint(0, 25),
            'error_rate': round(random.uniform(0, 2), 2),
            'response_time': f"{random.randint(50, 200)}ms"
        }
    })

@api_view(['GET'])
def migration_progress(request, project_id):
    """Migration progress tracking endpoint."""
    import random

    # Simulate different project states
    projects = {
        1: {'name': 'Customer Data Migration', 'status': 'in_progress', 'progress': 75},
        2: {'name': 'Legacy System Migration', 'status': 'completed', 'progress': 100},
        3: {'name': 'Analytics Migration', 'status': 'starting', 'progress': 5}
    }

    project = projects.get(project_id, {'name': 'Unknown Project', 'status': 'not_found', 'progress': 0})

    return Response({
        'project_id': project_id,
        'project_name': project['name'],
        'status': project['status'],
        'progress_percentage': project['progress'],
        'current_phase': 'Data Transfer' if project['progress'] < 80 else 'Validation',
        'estimated_completion': '2024-05-26T15:30:00Z',
        'records_processed': random.randint(10000, 100000),
        'records_total': random.randint(100000, 500000),
        'transfer_speed': f"{random.randint(500, 2000)} records/sec",
        'errors_count': random.randint(0, 10),
        'warnings_count': random.randint(0, 25)
    })

@api_view(['GET'])
def system_status(request):
    """Comprehensive system status endpoint."""
    return Response({
        'system': {
            'status': 'healthy',
            'version': '1.0.0',
            'uptime': '5 days, 12 hours, 34 minutes',
            'environment': 'development'
        },
        'services': {
            'database': {
                'status': 'online',
                'response_time': '15ms',
                'connections': 12,
                'health_score': 98
            },
            'redis': {
                'status': 'online',
                'response_time': '2ms',
                'memory_usage': '45%',
                'health_score': 99
            },
            'celery': {
                'status': 'online',
                'active_workers': 4,
                'pending_tasks': 3,
                'health_score': 95
            },
            'api': {
                'status': 'online',
                'response_time': '120ms',
                'requests_per_minute': 45,
                'health_score': 97
            }
        },
        'resources': {
            'cpu_usage': 45.2,
            'memory_usage': 62.8,
            'disk_usage': 34.1,
            'network_io': {
                'inbound': '1.2 MB/s',
                'outbound': '2.1 MB/s'
            }
        },
        'alerts': [
            {
                'level': 'info',
                'message': 'System performing optimally',
                'timestamp': '2024-05-26T11:30:00Z'
            }
        ]
    })

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Simple endpoints
    path('api/', api_root, name='api-root'),
    path('health/', health_check, name='health-check'),
    path('', api_root, name='root'),

    # Module endpoints
    path('api/modules/', modules_status, name='modules-status'),
    path('api/analyzer/status/', analyzer_status, name='analyzer-status'),
    path('api/orchestrator/status/', orchestrator_status, name='orchestrator-status'),
    path('api/validation/status/', validation_status, name='validation-status'),
    path('api/transformation/status/', transformation_status, name='transformation-status'),
    path('api/mapping/status/', mapping_status, name='mapping-status'),
    path('api/ml/status/', ml_status, name='ml-status'),

    # Data endpoints
    path('api/projects/', projects_api, name='projects-api'),
    path('api/datasources/', datasources_api, name='datasources-api'),

    # Authentication endpoints
    path('api/auth/login/', auth_login, name='auth-login'),
    path('api/auth/logout/', auth_logout, name='auth-logout'),
    path('api/auth/profile/', auth_profile, name='auth-profile'),

    # Analytics endpoints
    path('api/analytics/dashboard/', analytics_dashboard, name='analytics-dashboard'),
    path('api/system/metrics/', system_metrics, name='system-metrics'),
    path('api/analytics/realtime/', realtime_analytics, name='realtime-analytics'),
    path('api/migration/progress/<int:project_id>/', migration_progress, name='migration-progress'),
    path('api/system/status/', system_status, name='system-status'),
]
