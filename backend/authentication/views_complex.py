from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
from .models import User
# from .models import UserInvitation  # Temporarily disabled
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    PasswordChangeSerializer, LoginSerializer
    # UserInvitationSerializer, InvitationAcceptSerializer  # Temporarily disabled
)
from core.models import AuditLog


class UserProfileView(generics.RetrieveUpdateAPIView):
    """View for user profile management."""

    serializer_class = UserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserSerializer
        return UserUpdateSerializer


class PasswordChangeView(generics.GenericAPIView):
    """View for changing user password."""

    serializer_class = PasswordChangeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Log password change
        AuditLog.objects.create(
            tenant=request.tenant,
            user=request.user,
            action='password_changed',
            resource_type='user',
            resource_id=str(request.user.id),
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return Response({
            'message': _('Password changed successfully')
        })

    def _get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """User login endpoint."""
    serializer = LoginSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)

    user = serializer.validated_data['user']

    # Check if user belongs to the current tenant
    if hasattr(request, 'tenant') and user.tenant != request.tenant:
        return Response(
            {'error': _('User does not belong to this tenant')},
            status=status.HTTP_403_FORBIDDEN
        )

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token

    # Update user login info
    user.last_login = timezone.now()
    user.last_login_ip = request.META.get('REMOTE_ADDR')
    user.failed_login_attempts = 0
    user.save(update_fields=['last_login', 'last_login_ip', 'failed_login_attempts'])

    # Log successful login
    AuditLog.objects.create(
        tenant=getattr(request, 'tenant', None),
        user=user,
        action='login',
        resource_type='user',
        resource_id=str(user.id),
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
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
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()

        # Log logout
        AuditLog.objects.create(
            tenant=getattr(request, 'tenant', None),
            user=request.user,
            action='logout',
            resource_type='user',
            resource_id=str(request.user.id),
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return Response({'message': _('Logged out successfully')})
    except Exception as e:
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

    # Set tenant for the user
    user_data = serializer.validated_data
    if hasattr(request, 'tenant'):
        user_data['tenant'] = request.tenant

    user = serializer.save()

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token

    # Log registration
    AuditLog.objects.create(
        tenant=getattr(request, 'tenant', None),
        user=user,
        action='user_registered',
        resource_type='user',
        resource_id=str(user.id),
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    return Response({
        'access': str(access_token),
        'refresh': str(refresh),
        'user': UserSerializer(user).data
    }, status=status.HTTP_201_CREATED)


class UserInvitationListCreateView(generics.ListCreateAPIView):
    """View for listing and creating user invitations."""

    serializer_class = UserInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter invitations by tenant."""
        return UserInvitation.objects.filter(
            tenant=self.request.tenant
        ).order_by('-created_at')

    def perform_create(self, serializer):
        """Create invitation with current tenant and user."""
        # Check if user can manage users
        if not self.request.user.can_manage_users():
            raise permissions.PermissionDenied(
                _('You do not have permission to invite users')
            )

        # Set expiration date (7 days from now)
        expires_at = timezone.now() + timedelta(days=7)

        invitation = serializer.save(
            tenant=self.request.tenant,
            invited_by=self.request.user,
            expires_at=expires_at
        )

        # TODO: Send invitation email
        # send_invitation_email.delay(invitation.id)

        # Log invitation creation
        AuditLog.objects.create(
            tenant=self.request.tenant,
            user=self.request.user,
            action='invitation_created',
            resource_type='invitation',
            resource_id=str(invitation.id),
            metadata={
                'invited_email': invitation.email,
                'role': invitation.role
            }
        )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def accept_invitation_view(request, invitation_id):
    """Accept user invitation and create account."""
    try:
        invitation = UserInvitation.objects.get(
            id=invitation_id,
            status='pending'
        )
    except UserInvitation.DoesNotExist:
        return Response(
            {'error': _('Invalid or expired invitation')},
            status=status.HTTP_404_NOT_FOUND
        )

    # Check if invitation is expired
    if invitation.is_expired():
        invitation.status = 'expired'
        invitation.save()
        return Response(
            {'error': _('Invitation has expired')},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate and create user
    serializer = InvitationAcceptSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    # Create user
    user = User.objects.create_user(
        username=serializer.validated_data['username'],
        email=invitation.email,
        first_name=serializer.validated_data['first_name'],
        last_name=serializer.validated_data['last_name'],
        password=serializer.validated_data['password'],
        tenant=invitation.tenant,
        role=invitation.role,
        is_verified=True
    )

    # Update invitation status
    invitation.status = 'accepted'
    invitation.accepted_at = timezone.now()
    invitation.save()

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token

    # Log invitation acceptance
    AuditLog.objects.create(
        tenant=invitation.tenant,
        user=user,
        action='invitation_accepted',
        resource_type='invitation',
        resource_id=str(invitation.id)
    )

    return Response({
        'access': str(access_token),
        'refresh': str(refresh),
        'user': UserSerializer(user).data
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def invitation_detail_view(request, invitation_id):
    """Get invitation details for acceptance."""
    try:
        invitation = UserInvitation.objects.select_related('tenant').get(
            id=invitation_id,
            status='pending'
        )
    except UserInvitation.DoesNotExist:
        return Response(
            {'error': _('Invalid or expired invitation')},
            status=status.HTTP_404_NOT_FOUND
        )

    # Check if invitation is expired
    if invitation.is_expired():
        invitation.status = 'expired'
        invitation.save()
        return Response(
            {'error': _('Invitation has expired')},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response({
        'email': invitation.email,
        'role': invitation.role,
        'tenant_name': invitation.tenant.name,
        'invited_by': invitation.invited_by.get_full_name(),
        'expires_at': invitation.expires_at
    })