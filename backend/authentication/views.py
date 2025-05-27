from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
from .models import User
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    PasswordChangeSerializer, LoginSerializer
)
from core.models import AuditLog


class UserProfileView(generics.RetrieveUpdateAPIView):
    """View for user profile management."""
    
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Return the current user."""
        return self.request.user
    
    def get_serializer_class(self):
        """Return appropriate serializer based on request method."""
        if self.request.method == 'PATCH':
            return UserUpdateSerializer
        return UserSerializer


class UserListCreateView(generics.ListCreateAPIView):
    """View for listing and creating users."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on request method."""
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer
    
    def get_queryset(self):
        """Filter users by tenant and permissions."""
        if not self.request.user.can_manage_users():
            # Regular users can only see themselves
            return User.objects.filter(id=self.request.user.id)
        
        # Admins and managers can see all users in their tenant
        if hasattr(self.request, 'tenant') and self.request.tenant:
            return User.objects.filter(tenant=self.request.tenant)
        
        # Superusers can see all users
        if self.request.user.is_superuser:
            return User.objects.all()
        
        return User.objects.none()
    
    def perform_create(self, serializer):
        """Create user with current tenant."""
        # Check permissions
        if not self.request.user.can_manage_users():
            raise permissions.PermissionDenied(
                _('You do not have permission to create users')
            )
        
        # Set tenant if available
        tenant = getattr(self.request, 'tenant', None)
        user = serializer.save(tenant=tenant)
        
        # Log user creation
        if tenant:
            AuditLog.objects.create(
                tenant=tenant,
                user=self.request.user,
                action='user_created',
                resource_type='user',
                resource_id=str(user.id),
                metadata={
                    'created_user_email': user.email,
                    'role': user.role
                }
            )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password_view(request):
    """Change user password."""
    serializer = PasswordChangeSerializer(
        data=request.data,
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    
    # Log password change
    if hasattr(request, 'tenant') and request.tenant:
        AuditLog.objects.create(
            tenant=request.tenant,
            user=request.user,
            action='password_changed',
            resource_type='user',
            resource_id=str(request.user.id)
        )
    
    return Response({'message': _('Password changed successfully')})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """User login endpoint."""
    serializer = LoginSerializer(
        data=request.data,
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    
    user = serializer.validated_data['user']
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token
    
    # Log login
    if hasattr(request, 'tenant') and request.tenant:
        AuditLog.objects.create(
            tenant=request.tenant,
            user=user,
            action='login',
            resource_type='user',
            resource_id=str(user.id),
            metadata={
                'ip_address': request.META.get('REMOTE_ADDR'),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')
            }
        )
    
    return Response({
        'access': str(access_token),
        'refresh': str(refresh),
        'user': UserSerializer(user).data
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """User logout endpoint."""
    try:
        # Get refresh token from request
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        # Log logout
        if hasattr(request, 'tenant') and request.tenant:
            AuditLog.objects.create(
                tenant=request.tenant,
                user=request.user,
                action='logout',
                resource_type='user',
                resource_id=str(request.user.id)
            )
        
        return Response({'message': _('Logged out successfully')})
    except Exception:
        return Response(
            {'error': _('Error during logout')},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_view(request):
    """User registration endpoint."""
    serializer = UserCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    # Create user
    user = serializer.save()
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token
    
    # Log registration
    AuditLog.objects.create(
        user=user,
        action='user_registered',
        resource_type='user',
        resource_id=str(user.id),
        metadata={
            'email': user.email,
            'ip_address': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')
        }
    )
    
    return Response({
        'access': str(access_token),
        'refresh': str(refresh),
        'user': UserSerializer(user).data
    }, status=status.HTTP_201_CREATED)
