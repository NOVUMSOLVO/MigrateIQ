from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from .models import CustomDataConnector, SyncLog
from .serializers import CustomDataConnectorSerializer, SyncLogSerializer
from .services import DataSyncService
import time

class CustomDataConnectorViewSet(viewsets.ModelViewSet):
    """API endpoints for custom data connectors."""

    queryset = CustomDataConnector.objects.all()
    serializer_class = CustomDataConnectorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by tenant."""
        if hasattr(self.request.user, 'tenant'):
            return CustomDataConnector.objects.filter(tenant=self.request.user.tenant)
        return CustomDataConnector.objects.none()

    @extend_schema(
        summary="Test API connection",
        description="Test connection to the external API endpoint"
    )
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test connection to the API endpoint."""
        connector = self.get_object()
        service = DataSyncService(connector)

        start_time = time.time()
        try:
            is_connected = service.test_connection()
            duration = time.time() - start_time

            return Response({
                'connected': is_connected,
                'response_time_ms': round(duration * 1000, 2),
                'message': 'Connection successful' if is_connected else 'Connection failed',
                'endpoint': connector.api_endpoint
            })
        except Exception as e:
            return Response({
                'connected': False,
                'error': str(e),
                'message': 'Connection test failed'
            }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Sync data from API",
        description="Start data synchronization from the external API"
    )
    @action(detail=True, methods=['post'])
    def sync_data(self, request, pk=None):
        """Start data synchronization."""
        connector = self.get_object()
        service = DataSyncService(connector)

        try:
            sync_log = service.sync_data()
            serializer = SyncLogSerializer(sync_log)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'error': str(e),
                'message': 'Data synchronization failed'
            }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Get sync history",
        description="Get synchronization history for this connector"
    )
    @action(detail=True, methods=['get'])
    def sync_history(self, request, pk=None):
        """Get sync history for the connector."""
        connector = self.get_object()
        logs = connector.sync_logs.all()[:10]  # Last 10 sync attempts
        serializer = SyncLogSerializer(logs, many=True)
        return Response(serializer.data)

class SyncLogViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for sync logs."""

    queryset = SyncLog.objects.all()
    serializer_class = SyncLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by tenant through connector."""
        if hasattr(self.request.user, 'tenant'):
            return SyncLog.objects.filter(connector__tenant=self.request.user.tenant)
        return SyncLog.objects.none()
