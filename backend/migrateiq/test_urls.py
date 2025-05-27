"""
Test URL configuration for MigrateIQ backend.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/auth/', include('authentication.urls')),
    path('api/analyzer/', include('analyzer.urls')),
    path('api/orchestrator/', include('orchestrator.urls')),
    path('api/mapping/', include('mapping_engine.urls')),
    path('api/transformation/', include('transformation.urls')),
    path('api/validation/', include('validation.urls')),
    path('api/integrations/', include('integrations.urls')),
    # path('api/graphql/', include('graphql_api.urls')),  # Temporarily disabled for testing
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
