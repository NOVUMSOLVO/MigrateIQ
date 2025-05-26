"""
URL configuration for the transformation app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransformationRuleViewSet, TransformationJobViewSet, TransformationErrorViewSet

router = DefaultRouter()
router.register(r'rules', TransformationRuleViewSet)
router.register(r'jobs', TransformationJobViewSet)
router.register(r'errors', TransformationErrorViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
