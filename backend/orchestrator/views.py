"""
Views for the orchestrator app.
"""
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import MigrationProject, MigrationTask
from .serializers import MigrationProjectSerializer, MigrationProjectCreateSerializer, MigrationTaskSerializer
from .services import MigrationOrchestrator

class MigrationProjectViewSet(viewsets.ModelViewSet):
    """API endpoint for migration projects."""

    queryset = MigrationProject.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return MigrationProjectCreateSerializer
        return MigrationProjectSerializer

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start the migration process for a project."""
        project = self.get_object()

        # Check if the project is already in progress
        if project.status == 'IN_PROGRESS':
            return Response({
                'error': 'Project is already in progress'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            orchestrator = MigrationOrchestrator(project.id)
            success = orchestrator.start_migration()

            if success:
                return Response({
                    'message': 'Migration started successfully'
                })
            else:
                return Response({
                    'error': 'Migration failed to start'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """Get tasks for a project."""
        project = self.get_object()
        tasks = MigrationTask.objects.filter(project=project)
        serializer = MigrationTaskSerializer(tasks, many=True)

        return Response(serializer.data)

class MigrationTaskViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for migration tasks."""

    queryset = MigrationTask.objects.all()
    serializer_class = MigrationTaskSerializer
