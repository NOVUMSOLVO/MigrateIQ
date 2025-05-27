from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomDataConnectorViewSet, SyncLogViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'connectors', CustomDataConnectorViewSet, basename='connector')
router.register(r'sync-logs', SyncLogViewSet, basename='synclog')

# URL patterns
urlpatterns = [
    path('api/demo-extension/', include(router.urls)),
]
