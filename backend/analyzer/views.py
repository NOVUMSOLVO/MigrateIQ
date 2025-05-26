from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import DataSource, Entity, Field
from .serializers import DataSourceSerializer, DataSourceCreateSerializer, EntitySerializer, FieldSerializer
from .services import DataSourceAnalyzer, SchemaAnalyzer

class DataSourceViewSet(viewsets.ModelViewSet):
    """API endpoint for data sources."""

    queryset = DataSource.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return DataSourceCreateSerializer
        return DataSourceSerializer

    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        """Analyze a data source to extract schema information."""
        data_source = self.get_object()

        try:
            analyzer = DataSourceAnalyzer(data_source.id)
            entity = analyzer.analyze()

            return Response({
                'message': 'Data source analyzed successfully',
                'entity_id': entity.id
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class EntityViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for entities."""

    queryset = Entity.objects.all()
    serializer_class = EntitySerializer

    @action(detail=True, methods=['get'])
    def fields(self, request, pk=None):
        """Get fields for an entity."""
        entity = self.get_object()
        fields = Field.objects.filter(entity=entity)
        serializer = FieldSerializer(fields, many=True)

        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def compare(self, request, pk=None):
        """Compare this entity with another entity."""
        source_entity = self.get_object()
        target_entity_id = request.data.get('target_entity_id')

        if not target_entity_id:
            return Response({
                'error': 'target_entity_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            analyzer = SchemaAnalyzer()
            mappings = analyzer.compare_entities(source_entity.id, target_entity_id)

            return Response({
                'mappings': [
                    {
                        'source_field': mapping['source_field'].name,
                        'target_field': mapping['target_field'].name,
                        'confidence': mapping['confidence']
                    }
                    for mapping in mappings
                ]
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
