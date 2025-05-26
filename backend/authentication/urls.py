from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from . import views

app_name = 'authentication'

urlpatterns = [
    # JWT Token endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Authentication endpoints
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # User profile endpoints
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('password/change/', views.PasswordChangeView.as_view(), name='password_change'),
    
    # User invitation endpoints
    path('invitations/', views.UserInvitationListCreateView.as_view(), name='invitation_list_create'),
    path('invitations/<uuid:invitation_id>/', views.invitation_detail_view, name='invitation_detail'),
    path('invitations/<uuid:invitation_id>/accept/', views.accept_invitation_view, name='invitation_accept'),
]