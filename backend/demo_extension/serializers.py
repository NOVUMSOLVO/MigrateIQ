from rest_framework import serializers
from .models import CustomDataConnector, SyncLog

class CustomDataConnectorSerializer(serializers.ModelSerializer):
    """Serializer for custom data connectors."""
    
    class Meta:
        model = CustomDataConnector
        fields = [
            'id', 'name', 'api_endpoint', 'api_key', 'is_active',
            'sync_frequency', 'last_sync', 'records_synced',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'api_key': {'write_only': True},  # Don't expose API key in responses
        }
    
    def create(self, validated_data):
        """Create connector with current user's tenant."""
        request = self.context.get('request')
        if request and hasattr(request.user, 'tenant'):
            validated_data['tenant'] = request.user.tenant
        return super().create(validated_data)

class SyncLogSerializer(serializers.ModelSerializer):
    """Serializer for sync logs."""
    
    connector_name = serializers.CharField(source='connector.name', read_only=True)
    
    class Meta:
        model = SyncLog
        fields = [
            'id', 'connector', 'connector_name', 'status',
            'records_processed', 'error_message', 'duration_seconds',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class ConnectorStatsSerializer(serializers.Serializer):
    """Serializer for connector statistics."""
    
    total_connectors = serializers.IntegerField()
    active_connectors = serializers.IntegerField()
    total_records_synced = serializers.IntegerField()
    last_24h_syncs = serializers.IntegerField()
    success_rate = serializers.FloatField()
    avg_sync_duration = serializers.FloatField()
