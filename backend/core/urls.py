from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'core'

# Create router for ViewSets
router = DefaultRouter()
router.register(r'tenants', views.TenantViewSet, basename='tenant')
router.register(r'audit-logs', views.AuditLogViewSet, basename='auditlog')
router.register(r'features', views.FeatureViewSet, basename='feature')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # System configuration endpoints
    path('system/config/', views.SystemConfigurationListView.as_view(), name='system_config'),
    path('system/config/<str:key>/', views.SystemConfigurationDetailView.as_view(), name='system_config_detail'),
    
    # Tenant management endpoints
    path('tenant/current/', views.CurrentTenantView.as_view(), name='current_tenant'),
    path('tenant/settings/', views.TenantSettingsView.as_view(), name='tenant_settings'),
    path('tenant/usage/', views.TenantUsageView.as_view(), name='tenant_usage'),
    
    # Feature flag endpoints
    path('features/check/<str:feature_name>/', views.FeatureCheckView.as_view(), name='feature_check'),
    
    # Health check endpoint
    path('health/', views.HealthCheckView.as_view(), name='health_check'),
]