from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from .models import User
# from .models import UserInvitation, UserGroup, UserGroupMembership, UserActivity, UserSession  # Temporarily disabled


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    full_name = serializers.ReadOnlyField(source='get_full_name')

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'role', 'language', 'timezone', 'preferences',
            'is_verified', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_verified']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating users."""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'phone',
            'role', 'language', 'timezone', 'password', 'password_confirm'
        ]

    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(_("Passwords don't match"))
        return attrs

    def create(self, validated_data):
        """Create user with encrypted password."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'language',
            'timezone', 'preferences'
        ]


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for changing password."""

    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True)

    def validate_current_password(self, value):
        """Validate current password."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Current password is incorrect"))
        return value

    def validate(self, attrs):
        """Validate new password confirmation."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError(_("New passwords don't match"))
        return attrs

    def save(self):
        """Save new password."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)

    def validate(self, attrs):
        """Validate login credentials."""
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )

            if not user:
                raise serializers.ValidationError(
                    _("Unable to log in with provided credentials")
                )

            if not user.is_active:
                raise serializers.ValidationError(
                    _("User account is disabled")
                )

            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                _("Must include email and password")
            )


# Temporarily disabled until UserInvitation model is available
# class UserInvitationSerializer(serializers.ModelSerializer):
    """Serializer for UserInvitation model."""

    invited_by_name = serializers.ReadOnlyField(source='invited_by.get_full_name')
    tenant_name = serializers.ReadOnlyField(source='tenant.name')

    class Meta:
        model = UserInvitation
        fields = [
            'id', 'email', 'role', 'status', 'invited_by_name',
            'tenant_name', 'created_at', 'expires_at', 'accepted_at'
        ]
        read_only_fields = [
            'id', 'status', 'invited_by_name', 'tenant_name',
            'created_at', 'expires_at', 'accepted_at'
        ]


# Temporarily disabled until UserInvitation model is available
# class InvitationAcceptSerializer(serializers.Serializer):
    """Serializer for accepting invitations."""

    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)
    username = serializers.CharField(required=True, max_length=150)
    password = serializers.CharField(required=True, min_length=8)
    password_confirm = serializers.CharField(required=True)

    def validate_username(self, value):
        """Validate username uniqueness."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(_("Username already exists"))
        return value

    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(_("Passwords don't match"))
        return attrs


# Temporarily disabled until UserGroup model is available
# class UserGroupSerializer(serializers.ModelSerializer):
    """Serializer for UserGroup model."""

    member_count = serializers.SerializerMethodField()
    tenant_name = serializers.ReadOnlyField(source='tenant.name')

    class Meta:
        model = UserGroup
        fields = [
            'id', 'name', 'description', 'permissions', 'member_count',
            'tenant_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'member_count', 'tenant_name', 'created_at', 'updated_at']

    def get_member_count(self, obj):
        """Get the number of members in the group."""
        return obj.members.count()


# Temporarily disabled until UserGroupMembership model is available
# class UserGroupMembershipSerializer(serializers.ModelSerializer):
    """Serializer for UserGroupMembership model."""

    user_name = serializers.ReadOnlyField(source='user.get_full_name')
    user_email = serializers.ReadOnlyField(source='user.email')
    group_name = serializers.ReadOnlyField(source='group.name')

    class Meta:
        model = UserGroupMembership
        fields = [
            'id', 'user', 'group', 'role', 'user_name', 'user_email',
            'group_name', 'joined_at'
        ]
        read_only_fields = ['id', 'user_name', 'user_email', 'group_name', 'joined_at']


# Temporarily disabled until UserActivity model is available
# class UserActivitySerializer(serializers.ModelSerializer):
    """Serializer for UserActivity model."""

    user_name = serializers.ReadOnlyField(source='user.get_full_name')
    user_email = serializers.ReadOnlyField(source='user.email')
    tenant_name = serializers.ReadOnlyField(source='tenant.name')

    class Meta:
        model = UserActivity
        fields = [
            'id', 'activity_type', 'description', 'ip_address', 'user_agent',
            'session_key', 'metadata', 'timestamp', 'user_name', 'user_email',
            'tenant_name'
        ]
        read_only_fields = [
            'id', 'timestamp', 'user_name', 'user_email', 'tenant_name'
        ]


# Temporarily disabled until UserSession model is available
# class UserSessionSerializer(serializers.ModelSerializer):
    """Serializer for UserSession model."""

    user_name = serializers.ReadOnlyField(source='user.get_full_name')
    user_email = serializers.ReadOnlyField(source='user.email')
    is_expired_flag = serializers.SerializerMethodField()

    class Meta:
        model = UserSession
        fields = [
            'id', 'session_key', 'ip_address', 'user_agent', 'device_info',
            'country', 'city', 'is_active', 'last_activity', 'created_at',
            'expires_at', 'user_name', 'user_email', 'is_expired_flag'
        ]
        read_only_fields = [
            'id', 'session_key', 'last_activity', 'created_at', 'user_name',
            'user_email', 'is_expired_flag'
        ]

    def get_is_expired_flag(self, obj):
        """Check if session is expired."""
        return obj.is_expired()