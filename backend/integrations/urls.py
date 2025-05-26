"""
URL configuration for integrations app.
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

# Create a router for ViewSets
router = DefaultRouter()

urlpatterns = [
    # Integrations endpoints will be added here
    # For now, just include the router URLs
] + router.urls
