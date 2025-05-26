"""
Views for the mapping_engine app.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from analyzer.models import Entity
from .models import Mapping, FieldMapping, MappingRule
from .serializers import MappingSerializer, FieldMappingSerializer, MappingRuleSerializer
from .services import MappingEngine


class MappingViewSet(viewsets.ModelViewSet):
    """ViewSet for Mapping model."""
    
    queryset = Mapping.objects.all()
    serializer_class = MappingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset to only show mappings for projects created by the current user."""
        return Mapping.objects.filter(source_entity__source_system__project__created_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate mappings between source and target entities."""
        source_entity_ids = request.data.get('source_entity_ids', [])
        target_entity_ids = request.data.get('target_entity_ids', [])
        
        if not source_entity_ids or not target_entity_ids:
            return Response(
                {'error': 'Source and target entity IDs are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            source_entities = Entity.objects.filter(id__in=source_entity_ids)
            target_entities = Entity.objects.filter(id__in=target_entity_ids)
            
            mapping_engine = MappingEngine()
            mappings = mapping_engine.generate_entity_mappings(source_entities, target_entities)
            
            # Save mappings to database
            for mapping in mappings:
                mapping.save()
                
                # Generate field mappings
                field_mappings = mapping_engine.generate_field_mappings(mapping)
                for field_mapping in field_mappings:
                    field_mapping.save()
            
            # Return the created mappings
            serializer = MappingSerializer(mappings, many=True)
            return Response(serializer.data)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FieldMappingViewSet(viewsets.ModelViewSet):
    """ViewSet for FieldMapping model."""
    
    queryset = FieldMapping.objects.all()
    serializer_class = FieldMappingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset to only show field mappings for projects created by the current user."""
        return FieldMapping.objects.filter(
            mapping__source_entity__source_system__project__created_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Mark a field mapping as manually verified."""
        field_mapping = self.get_object()
        field_mapping.is_manually_verified = True
        field_mapping.save()
        
        serializer = self.get_serializer(field_mapping)
        return Response(serializer.data)


class MappingRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for MappingRule model."""
    
    queryset = MappingRule.objects.all()
    serializer_class = MappingRuleSerializer
    permission_classes = [permissions.IsAuthenticated]
