from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'system-metrics', views.SystemMetricViewSet, basename='system-metric')
router.register(r'tenant-metrics', views.TenantMetricViewSet, basename='tenant-metric')
router.register(r'performance-logs', views.PerformanceLogViewSet, basename='performance-log')
router.register(r'alerts', views.AlertViewSet, basename='alert')
router.register(r'health-check-results', views.HealthCheckResultViewSet, basename='health-check-result')

urlpatterns = [
    path('', include(router.urls)),
    path('health/', views.SystemHealthView.as_view(), name='system-health'),
    path('metrics/', views.MetricsExportView.as_view(), name='metrics-export'),
]