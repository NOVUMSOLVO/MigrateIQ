from rest_framework import generics, viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from datetime import timedelta
import hashlib
from .models import Tenant, AuditLog, SystemConfiguration, Feature
from .serializers import (
    TenantSerializer, AuditLogSerializer, SystemConfigurationSerializer,
    FeatureSerializer, TenantUsageSerializer
)
from .permissions import IsSuperUserOrTenantAdmin, IsSuperUser


class TenantViewSet(viewsets.ModelViewSet):
    """ViewSet for managing tenants."""
    
    serializer_class = TenantSerializer
    permission_classes = [IsSuperUser]
    
    def get_queryset(self):
        """Return all tenants for superusers."""
        return Tenant.objects.all().order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a tenant."""
        tenant = self.get_object()
        tenant.is_active = True
        tenant.save()
        
        AuditLog.objects.create(
            tenant=tenant,
            user=request.user,
            action='tenant_activated',
            resource_type='tenant',
            resource_id=str(tenant.id)
        )
        
        return Response({'message': _('Tenant activated successfully')})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a tenant."""
        tenant = self.get_object()
        tenant.is_active = False
        tenant.save()
        
        AuditLog.objects.create(
            tenant=tenant,
            user=request.user,
            action='tenant_deactivated',
            resource_type='tenant',
            resource_id=str(tenant.id)
        )
        
        return Response({'message': _('Tenant deactivated successfully')})
    
    @action(detail=True, methods=['get'])
    def usage(self, request, pk=None):
        """Get tenant usage statistics."""
        tenant = self.get_object()
        
        # Calculate usage statistics
        user_count = tenant.users.count()
        project_count = tenant.projects.count() if hasattr(tenant, 'projects') else 0
        data_source_count = tenant.data_sources.count() if hasattr(tenant, 'data_sources') else 0
        
        # Calculate storage usage (placeholder)
        storage_used_gb = 0  # TODO: Implement actual storage calculation
        
        usage_data = {
            'user_count': user_count,
            'max_users': tenant.max_users,
            'project_count': project_count,
            'max_projects': tenant.max_projects,
            'data_source_count': data_source_count,
            'max_data_sources': tenant.max_data_sources,
            'storage_used_gb': storage_used_gb,
            'storage_limit_gb': tenant.storage_limit_gb,
            'subscription_plan': tenant.subscription_plan,
            'subscription_expires_at': tenant.subscription_expires_at,
        }
        
        serializer = TenantUsageSerializer(usage_data)
        return Response(serializer.data)


class CurrentTenantView(generics.RetrieveUpdateAPIView):
    """View for current tenant information."""
    
    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Return the current tenant."""
        if hasattr(self.request, 'tenant'):
            return self.request.tenant
        return None


class TenantSettingsView(APIView):
    """View for managing tenant settings."""
    
    permission_classes = [IsSuperUserOrTenantAdmin]
    
    def get(self, request):
        """Get tenant settings."""
        if not hasattr(request, 'tenant') or not request.tenant:
            return Response(
                {'error': _('No tenant found')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(request.tenant.settings or {})
    
    def patch(self, request):
        """Update tenant settings."""
        if not hasattr(request, 'tenant') or not request.tenant:
            return Response(
                {'error': _('No tenant found')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        tenant = request.tenant
        current_settings = tenant.settings or {}
        current_settings.update(request.data)
        tenant.settings = current_settings
        tenant.save()
        
        AuditLog.objects.create(
            tenant=tenant,
            user=request.user,
            action='tenant_settings_updated',
            resource_type='tenant',
            resource_id=str(tenant.id),
            metadata={'updated_settings': request.data}
        )
        
        return Response(current_settings)


class TenantUsageView(APIView):
    """View for tenant usage statistics."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get current tenant usage."""
        if not hasattr(request, 'tenant') or not request.tenant:
            return Response(
                {'error': _('No tenant found')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        tenant = request.tenant
        
        # Calculate usage statistics
        user_count = tenant.users.count()
        project_count = tenant.projects.count() if hasattr(tenant, 'projects') else 0
        data_source_count = tenant.data_sources.count() if hasattr(tenant, 'data_sources') else 0
        
        # Calculate storage usage (placeholder)
        storage_used_gb = 0  # TODO: Implement actual storage calculation
        
        usage_data = {
            'user_count': user_count,
            'max_users': tenant.max_users,
            'project_count': project_count,
            'max_projects': tenant.max_projects,
            'data_source_count': data_source_count,
            'max_data_sources': tenant.max_data_sources,
            'storage_used_gb': storage_used_gb,
            'storage_limit_gb': tenant.storage_limit_gb,
            'subscription_plan': tenant.subscription_plan,
            'subscription_expires_at': tenant.subscription_expires_at,
        }
        
        serializer = TenantUsageSerializer(usage_data)
        return Response(serializer.data)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing audit logs."""
    
    serializer_class = AuditLogSerializer
    permission_classes = [IsSuperUserOrTenantAdmin]
    
    def get_queryset(self):
        """Filter audit logs by tenant."""
        queryset = AuditLog.objects.select_related('user', 'tenant').order_by('-timestamp')
        
        if self.request.user.is_superuser:
            return queryset
        
        if hasattr(self.request, 'tenant') and self.request.tenant:
            return queryset.filter(tenant=self.request.tenant)
        
        return queryset.none()
    
    def list(self, request, *args, **kwargs):
        """List audit logs with filtering."""
        queryset = self.get_queryset()
        
        # Apply filters
        action = request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        resource_type = request.query_params.get('resource_type')
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        
        user_id = request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Date range filtering
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        return super().list(request, *args, **kwargs)


class SystemConfigurationListView(generics.ListAPIView):
    """View for listing system configurations."""
    
    serializer_class = SystemConfigurationSerializer
    permission_classes = [IsSuperUser]
    
    def get_queryset(self):
        """Return active system configurations."""
        return SystemConfiguration.objects.filter(is_active=True).order_by('key')


class SystemConfigurationDetailView(generics.RetrieveUpdateAPIView):
    """View for managing individual system configuration."""
    
    serializer_class = SystemConfigurationSerializer
    permission_classes = [IsSuperUser]
    lookup_field = 'key'
    
    def get_queryset(self):
        """Return system configurations."""
        return SystemConfiguration.objects.all()


class FeatureViewSet(viewsets.ModelViewSet):
    """ViewSet for managing feature flags."""
    
    serializer_class = FeatureSerializer
    permission_classes = [IsSuperUser]
    
    def get_queryset(self):
        """Return all feature flags."""
        return Feature.objects.all().order_by('name')
    
    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        """Toggle feature flag status."""
        feature = self.get_object()
        feature.is_enabled = not feature.is_enabled
        feature.save()
        
        AuditLog.objects.create(
            user=request.user,
            action='feature_toggled',
            resource_type='feature',
            resource_id=str(feature.id),
            metadata={
                'feature_name': feature.name,
                'new_status': feature.is_enabled
            }
        )
        
        return Response({
            'message': _('Feature flag toggled successfully'),
            'is_enabled': feature.is_enabled
        })


class FeatureCheckView(APIView):
    """View for checking if a feature is enabled for current tenant."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, feature_name):
        """Check if feature is enabled for current tenant."""
        # Create cache key
        tenant_id = getattr(request.tenant, 'id', 'no_tenant')
        cache_key = f'feature_check_{feature_name}_{tenant_id}'
        
        # Try to get from cache first
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return Response({'enabled': cached_result})
        
        try:
            feature = Feature.objects.get(name=feature_name)
        except Feature.DoesNotExist:
            # Feature doesn't exist, assume disabled
            cache.set(cache_key, False, 300)  # Cache for 5 minutes
            return Response({'enabled': False})
        
        # Check if feature is enabled
        if not feature.is_enabled:
            cache.set(cache_key, False, 300)
            return Response({'enabled': False})
        
        # Check if tenant is whitelisted
        if hasattr(request, 'tenant') and request.tenant:
            if feature.whitelisted_tenants.filter(id=request.tenant.id).exists():
                cache.set(cache_key, True, 300)
                return Response({'enabled': True})
        
        # Check rollout percentage
        if feature.rollout_percentage >= 100:
            cache.set(cache_key, True, 300)
            return Response({'enabled': True})
        
        if feature.rollout_percentage <= 0:
            cache.set(cache_key, False, 300)
            return Response({'enabled': False})
        
        # Use deterministic hash for consistent rollout
        hash_input = f'{feature_name}_{tenant_id}'
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        percentage = (hash_value % 100) + 1
        
        enabled = percentage <= feature.rollout_percentage
        cache.set(cache_key, enabled, 300)
        
        return Response({'enabled': enabled})


class HealthCheckView(APIView):
    """Health check endpoint."""
    
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Return system health status."""
        health_data = {
            'status': 'healthy',
            'timestamp': timezone.now(),
            'version': getattr(settings, 'VERSION', '1.0.0'),
            'environment': getattr(settings, 'ENVIRONMENT', 'development'),
        }
        
        # Check database connectivity
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            health_data['database'] = 'connected'
        except Exception as e:
            health_data['database'] = 'error'
            health_data['status'] = 'unhealthy'
        
        # Check cache connectivity
        try:
            cache.set('health_check', 'ok', 10)
            if cache.get('health_check') == 'ok':
                health_data['cache'] = 'connected'
            else:
                health_data['cache'] = 'error'
                health_data['status'] = 'degraded'
        except Exception as e:
            health_data['cache'] = 'error'
            health_data['status'] = 'degraded'
        
        status_code = status.HTTP_200_OK
        if health_data['status'] == 'unhealthy':
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        elif health_data['status'] == 'degraded':
            status_code = status.HTTP_206_PARTIAL_CONTENT
        
        return Response(health_data, status=status_code)