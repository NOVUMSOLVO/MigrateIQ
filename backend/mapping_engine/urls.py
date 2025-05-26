"""
URL configuration for the mapping_engine app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MappingViewSet, FieldMappingViewSet, MappingRuleViewSet

router = DefaultRouter()
router.register(r'mappings', MappingViewSet)
router.register(r'field-mappings', FieldMappingViewSet)
router.register(r'rules', MappingRuleViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
