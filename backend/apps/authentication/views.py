from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom login view that sets JWT tokens in HttpOnly cookies
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh')
            
            # Create response without tokens in body
            res = Response({
                'message': 'Login successful',
                'detail': 'Tokens set in cookies'
            }, status=status.HTTP_200_OK)
            
            # Set access token in HttpOnly cookie
            res.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,          # Cannot be accessed by JavaScript
                secure=not settings.DEBUG,  # HTTPS only in production
                samesite='Lax',         # CSRF protection
                max_age=3600,           # 1 hour
                path='/',
                domain='localhost',
            )
            
            # Set refresh token in HttpOnly cookie
            res.set_cookie(
                key='refresh_token',
                value=refresh_token,
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                max_age=604800,         # 7 days
                path='/',
                domain='localhost',
            )
            
            return res
        
        return response


class CustomTokenRefreshView(TokenRefreshView):
    """
    Custom refresh view that reads refresh token from cookie
    """
    def post(self, request, *args, **kwargs):
        # Get refresh token from cookie
        refresh_token = request.COOKIES.get('refresh_token')
        
        if not refresh_token:
            return Response(
                {'detail': 'Refresh token not found in cookies'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Add refresh token to request data
        request.data['refresh'] = refresh_token
        
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            access_token = response.data.get('access')
            
            # Create response
            res = Response({
                'message': 'Token refreshed successfully'
            }, status=status.HTTP_200_OK)
            
            # Update access token cookie
            res.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                max_age=3600,
                path='/',
                domain='localhost',
            )
            
            return res
        
        return response


class LogoutView(TokenRefreshView):
    """
    Logout view that clears cookies
    """
    def post(self, request, *args, **kwargs):
        response = Response({
            'message': 'Logged out successfully'
        }, status=status.HTTP_200_OK)
        
        # Clear cookies
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        
        return response