"""
URL configuration for the orchestrator app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MigrationProjectViewSet, MigrationTaskViewSet

router = DefaultRouter()
router.register(r'projects', MigrationProjectViewSet)
router.register(r'tasks', MigrationTaskViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
