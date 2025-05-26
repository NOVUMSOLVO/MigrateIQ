"""
URL configuration for migrateiq project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.utils.translation import gettext_lazy as _
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

# Admin site customization
admin.site.site_header = _('MigrateIQ Administration')
admin.site.site_title = _('MigrateIQ Admin')
admin.site.index_title = _('Welcome to MigrateIQ Administration')

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Authentication endpoints
    path('api/auth/', include('authentication.urls')),

    # Core system endpoints
    path('api/core/', include('core.urls')),

    # Application endpoints
    path('api/analyzer/', include('analyzer.urls')),
    path('api/orchestrator/', include('orchestrator.urls')),
    path('api/validation/', include('validation.urls')),
    path('api/ml/', include('ml.urls')),

    # GraphQL endpoint (temporarily disabled due to schema issues)
    # path('api/', include('graphql_api.urls')),

    # Internationalization
    path('i18n/', include('django.conf.urls.i18n')),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Add debug toolbar if available
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
