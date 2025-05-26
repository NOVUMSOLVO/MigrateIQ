"""
Views for the validation app.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ValidationRule, ValidationJob, ValidationError
from .serializers import ValidationRuleSerializer, ValidationJobSerializer, ValidationErrorSerializer


class ValidationRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for ValidationRule model."""
    
    queryset = ValidationRule.objects.all()
    serializer_class = ValidationRuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset to only show rules for projects created by the current user."""
        return ValidationRule.objects.filter(
            entity_mapping__source_entity__source_system__project__created_by=self.request.user
        )


class ValidationJobViewSet(viewsets.ModelViewSet):
    """ViewSet for ValidationJob model."""
    
    queryset = ValidationJob.objects.all()
    serializer_class = ValidationJobSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset to only show jobs for projects created by the current user."""
        return ValidationJob.objects.filter(project__created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start a validation job."""
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


class ValidationErrorViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for ValidationError model."""
    
    queryset = ValidationError.objects.all()
    serializer_class = ValidationErrorSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset to only show errors for projects created by the current user."""
        return ValidationError.objects.filter(job__project__created_by=self.request.user)
