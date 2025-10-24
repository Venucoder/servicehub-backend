from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView, UserRegistrationView,
    EmailVerificationView, PhoneVerificationRequestView,
    PhoneVerificationConfirmView, PasswordResetRequestView,
    PasswordResetConfirmView, logout_view
)

app_name = 'authentication'

urlpatterns = [
    # JWT Authentication
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', logout_view, name='logout'),
    
    # Registration
    path('register/', UserRegistrationView.as_view(), name='register'),
    
    # Email Verification
    path('verify-email/', EmailVerificationView.as_view(), name='verify_email'),
    
    # Phone Verification
    path('verify-phone/request/', PhoneVerificationRequestView.as_view(), name='verify_phone_request'),
    path('verify-phone/confirm/', PhoneVerificationConfirmView.as_view(), name='verify_phone_confirm'),
    
    # Password Reset
    path('password-reset/request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]