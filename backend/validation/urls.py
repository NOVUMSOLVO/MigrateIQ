"""
URL configuration for the validation app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ValidationRuleViewSet, ValidationJobViewSet, ValidationErrorViewSet

router = DefaultRouter()
router.register(r'rules', ValidationRuleViewSet)
router.register(r'jobs', ValidationJobViewSet)
router.register(r'errors', ValidationErrorViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
