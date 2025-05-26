"""
URL configuration for the analyzer app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DataSourceViewSet, EntityViewSet

router = DefaultRouter()
router.register(r'data-sources', DataSourceViewSet)
router.register(r'entities', EntityViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
