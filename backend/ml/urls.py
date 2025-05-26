"""
URL configuration for the ML app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'ml'

# Create router for ViewSets (when views are implemented)
router = DefaultRouter()
# router.register(r'models', views.MLModelViewSet, basename='mlmodel')
# router.register(r'predictions', views.PredictionViewSet, basename='prediction')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),

    # ML service endpoints (placeholder for future implementation)
    # path('analyze/', views.analyze_data, name='analyze_data'),
    # path('predict/', views.predict_schema, name='predict_schema'),
    # path('quality/', views.assess_quality, name='assess_quality'),
]
