from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate, get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import (
    EmailVerificationToken, PhoneVerificationToken, 
    PasswordResetToken, LoginAttempt, UserSession
)
from .serializers import (
    CustomTokenObtainPairSerializer, UserRegistrationSerializer,
    EmailVerificationSerializer, PhoneVerificationSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer
)
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token view with additional user data
    """
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Log successful login
            user = User.objects.get(email=request.data.get('email'))
            LoginAttempt.objects.create(
                user=user,
                email=request.data.get('email'),
                attempt_type='success',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
            
            # Create or update session
            session_key = request.session.session_key
            if session_key:
                UserSession.objects.update_or_create(
                    user=user,
                    session_key=session_key,
                    defaults={
                        'ip_address': self.get_client_ip(request),
                        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                        'is_active': True,
                        'last_activity': timezone.now(),
                    }
                )
        else:
            # Log failed login
            LoginAttempt.objects.create(
                email=request.data.get('email', ''),
                attempt_type='failed_password',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
        
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserRegistrationView(APIView):
    """
    User registration endpoint
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Create email verification token
            email_token = EmailVerificationToken.objects.create(user=user)
            
            # Send verification email
            self.send_verification_email(user, email_token.token)
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'Registration successful. Please check your email for verification.',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'is_email_verified': user.is_email_verified,
                },
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def send_verification_email(self, user, token):
        """Send email verification email"""
        try:
            verification_url = f"{settings.FRONTEND_URL}/verify-email/{token}"
            send_mail(
                subject='Verify your ServiceHub account',
                message=f'Please click the following link to verify your email: {verification_url}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send verification email: {e}")


class EmailVerificationView(APIView):
    """
    Email verification endpoint
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            
            try:
                email_token = EmailVerificationToken.objects.get(
                    token=token,
                    is_used=False
                )
                
                if email_token.is_expired():
                    return Response({
                        'error': 'Verification token has expired.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Mark user as verified
                user = email_token.user
                user.is_email_verified = True
                user.save()
                
                # Mark token as used
                email_token.is_used = True
                email_token.save()
                
                return Response({
                    'message': 'Email verified successfully.'
                }, status=status.HTTP_200_OK)
                
            except EmailVerificationToken.DoesNotExist:
                return Response({
                    'error': 'Invalid verification token.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PhoneVerificationRequestView(APIView):
    """
    Request phone verification OTP
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response({
                'error': 'Phone number is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create verification token
        phone_token = PhoneVerificationToken.objects.create(
            user=request.user,
            phone_number=phone_number
        )
        
        # Send SMS (implement with your SMS provider)
        self.send_verification_sms(phone_number, phone_token.token)
        
        return Response({
            'message': 'Verification code sent to your phone.'
        }, status=status.HTTP_200_OK)
    
    def send_verification_sms(self, phone_number, token):
        """Send SMS verification code"""
        # Implement with your SMS provider (Twilio, AWS SNS, etc.)
        logger.info(f"SMS verification code {token} sent to {phone_number}")


class PhoneVerificationConfirmView(APIView):
    """
    Confirm phone verification with OTP
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PhoneVerificationSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            token = serializer.validated_data['token']
            
            try:
                phone_token = PhoneVerificationToken.objects.get(
                    user=request.user,
                    phone_number=phone_number,
                    token=token,
                    is_used=False
                )
                
                if phone_token.is_expired():
                    return Response({
                        'error': 'Verification code has expired.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                if phone_token.is_max_attempts_reached():
                    return Response({
                        'error': 'Maximum verification attempts reached.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Mark user phone as verified
                user = request.user
                user.phone = phone_number
                user.is_phone_verified = True
                user.save()
                
                # Mark token as used
                phone_token.is_used = True
                phone_token.save()
                
                return Response({
                    'message': 'Phone number verified successfully.'
                }, status=status.HTTP_200_OK)
                
            except PhoneVerificationToken.DoesNotExist:
                return Response({
                    'error': 'Invalid verification code.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """
    Request password reset
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email)
                
                # Create password reset token
                reset_token = PasswordResetToken.objects.create(user=user)
                
                # Send reset email
                self.send_reset_email(user, reset_token.token)
                
                return Response({
                    'message': 'Password reset instructions sent to your email.'
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                # Don't reveal if email exists
                return Response({
                    'message': 'Password reset instructions sent to your email.'
                }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def send_reset_email(self, user, token):
        """Send password reset email"""
        try:
            reset_url = f"{settings.FRONTEND_URL}/reset-password/{token}"
            send_mail(
                subject='Reset your ServiceHub password',
                message=f'Please click the following link to reset your password: {reset_url}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send reset email: {e}")


class PasswordResetConfirmView(APIView):
    """
    Confirm password reset
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            password = serializer.validated_data['password']
            
            try:
                reset_token = PasswordResetToken.objects.get(
                    token=token,
                    is_used=False
                )
                
                if reset_token.is_expired():
                    return Response({
                        'error': 'Reset token has expired.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Reset password
                user = reset_token.user
                user.set_password(password)
                user.save()
                
                # Mark token as used
                reset_token.is_used = True
                reset_token.save()
                
                return Response({
                    'message': 'Password reset successfully.'
                }, status=status.HTTP_200_OK)
                
            except PasswordResetToken.DoesNotExist:
                return Response({
                    'error': 'Invalid reset token.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    Logout endpoint - blacklist refresh token
    """
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        # Deactivate session
        session_key = request.session.session_key
        if session_key:
            UserSession.objects.filter(
                user=request.user,
                session_key=session_key
            ).update(is_active=False)
        
        return Response({
            'message': 'Logged out successfully.'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Invalid token.'
        }, status=status.HTTP_400_BAD_REQUEST)
