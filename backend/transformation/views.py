"""
Views for the transformation app.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import TransformationRule, TransformationJob, TransformationError
from .serializers import TransformationRuleSerializer, TransformationJobSerializer, TransformationErrorSerializer


class TransformationRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for TransformationRule model."""
    
    queryset = TransformationRule.objects.all()
    serializer_class = TransformationRuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset to only show rules for projects created by the current user."""
        return TransformationRule.objects.filter(
            field_mapping__mapping__source_entity__source_system__project__created_by=self.request.user
        )


class TransformationJobViewSet(viewsets.ModelViewSet):
    """ViewSet for TransformationJob model."""
    
    queryset = TransformationJob.objects.all()
    serializer_class = TransformationJobSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset to only show jobs for projects created by the current user."""
        return TransformationJob.objects.filter(project__created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start a transformation job."""
        job = self.get_object()
        
        if job.status != 'PENDING':
            return Response(
                {'error': 'Job can only be started when in PENDING status.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # In a real implementation, this would start a Celery task
        # For now, we'll just update the status
        job.status = 'IN_PROGRESS'
        job.started_at = datetime.now()
        job.save()
        
        return Response({'status': 'Job started'})


class TransformationErrorViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for TransformationError model."""
    
    queryset = TransformationError.objects.all()
    serializer_class = TransformationErrorSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset to only show errors for projects created by the current user."""
        return TransformationError.objects.filter(job__project__created_by=self.request.user)
