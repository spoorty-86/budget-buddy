from django.contrib.auth import get_user_model
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import Profile
from .serializers import RegisterSerializer, ProfileSerializer, PasswordResetSerializer, CustomTokenObtainPairSerializer
from notifications.models import Notification as UserNotification

User = get_user_model()


import logging
import traceback

logger = logging.getLogger(__name__)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Public token obtain endpoint -- disables authentication check so expired headers don't block login."""
    authentication_classes = []
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except Exception as exc:
            if 'no such table' in str(exc).lower():
                try:
                    from django.core.management import call_command
                    call_command('migrate', interactive=False)
                    return super().post(request, *args, **kwargs)
                except Exception:
                    pass
            raise exc


class CustomTokenRefreshView(TokenRefreshView):
    """Public token refresh endpoint -- disables authentication check so expired headers don't block refresh."""
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except User.DoesNotExist:
            return Response({'detail': 'User account for this refresh token no longer exists. Please log in again.'}, status=401)
        except Exception as exc:
            if 'does not exist' in str(exc).lower():
                return Response({'detail': 'Invalid or expired token. Please log in again.'}, status=401)
            raise exc



class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/  -- Milestone 1: user registration"""
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except Exception as exc:
            from rest_framework.exceptions import APIException
            if isinstance(exc, APIException):
                raise exc
            if 'no such table' in str(exc).lower():
                try:
                    from django.core.management import call_command
                    call_command('migrate', interactive=False)
                    return super().post(request, *args, **kwargs)
                except Exception as m_exc:
                    exc = m_exc
            tb = traceback.format_exc()
            logger.error("Registration Exception: %s\n%s", exc, tb)
            return Response({
                'detail': f"Server Error: {str(exc)}",
                'error_type': exc.__class__.__name__,
                'traceback': tb
            }, status=500)

    def perform_create(self, serializer):
        user = serializer.save()
        try:
            UserNotification.objects.create(
                user=user,
                title='Welcome to BudgetBuddy',
                message='Welcome to BudgetBuddy! Your account has been created successfully. You can now log in with your username and password and start managing your budget.',
                notification_type='SUCCESS',
            )
        except Exception:
            pass


class MeView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/auth/me/  -- current user's profile"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile


class DebugCurrentUserView(APIView):
    """GET /api/auth/debug-current-user/  -- Diagnostic endpoint for verifying production user authentication & DB email."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        email = (getattr(user, 'email', '') or '').strip()
        domain = email.split('@')[-1] if '@' in email else 'none'
        return Response({
            'authenticated': True,
            'user_id': user.id,
            'username': user.username,
            'email': email,
            'email_domain': domain,
        })



class PasswordResetView(APIView):
    """POST /api/auth/password-reset/  -- reset password by username and email"""
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        email = serializer.validated_data['email']
        new_password = serializer.validated_data['new_password']

        user = User.objects.filter(username__iexact=username, email__iexact=email).first()
        if not user:
            return Response({'detail': 'No matching account found for the provided username and email.'}, status=400)

        user.set_password(new_password)
        user.save()

        # Creating a UserNotification automatically triggers the email signal
        UserNotification.objects.create(
            user=user,
            title='Password Reset',
            message='Your BudgetBuddy password was reset successfully. If you did not request this change, please contact support immediately.',
            notification_type='INFO',
        )

        return Response({'detail': 'Password reset successfully. You can now log in with your new password.'})


import os
from dotenv import load_dotenv
from rest_framework_simplejwt.tokens import RefreshToken
from .oauth import get_google_user_info, get_github_user_info, get_or_create_oauth_user


class OAuthUrlsView(APIView):
    """GET /api/auth/oauth/urls/  -- Returns OAuth configuration and app IDs."""
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from pathlib import Path
        env_path = Path(__file__).resolve().parent.parent / '.env'
        load_dotenv(env_path, override=True)
        google_client_id = os.environ.get('GOOGLE_CLIENT_ID', '').strip()
        github_client_id = os.environ.get('GITHUB_CLIENT_ID', '').strip()
        return Response({
            'google_client_id': google_client_id,
            'github_client_id': github_client_id,
            'google_enabled': bool(google_client_id),
            'github_enabled': bool(github_client_id),
        })


class OAuthLoginView(APIView):
    """POST /api/auth/oauth/  -- Exchange OAuth code for SimpleJWT tokens."""
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        provider = request.data.get('provider')
        code = request.data.get('code')
        redirect_uri = request.data.get('redirect_uri')

        if not provider or not code:
            return Response({'detail': 'Both "provider" and "code" parameters are required.'}, status=400)

        if not redirect_uri:
            redirect_uri = request.build_absolute_uri('/')

        try:
            if provider == 'google':
                user_data = get_google_user_info(code, redirect_uri)
            elif provider == 'github':
                user_data = get_github_user_info(code, redirect_uri)
            else:
                return Response({'detail': f'Unsupported OAuth provider: "{provider}".'}, status=400)

            user = get_or_create_oauth_user(
                provider=provider,
                email=user_data['email'],
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
                avatar=user_data.get('avatar', ''),
                username_hint=user_data.get('username_hint', '')
            )

            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            })
        except ValueError as ve:
            logger.warning(f"OAuth validation error ({provider}): {ve}")
            return Response({'detail': str(ve)}, status=400)
        except Exception as exc:
            if 'no such table' in str(exc).lower():
                try:
                    from django.core.management import call_command
                    call_command('migrate', interactive=False)
                    user = get_or_create_oauth_user(
                        provider=provider,
                        email=user_data['email'],
                        first_name=user_data.get('first_name', ''),
                        last_name=user_data.get('last_name', ''),
                        avatar=user_data.get('avatar', ''),
                        username_hint=user_data.get('username_hint', '')
                    )
                    refresh = RefreshToken.for_user(user)
                    return Response({
                        'access': str(refresh.access_token),
                        'refresh': str(refresh),
                    })
                except Exception as m_exc:
                    exc = m_exc
            tb = traceback.format_exc()
            logger.error(f"OAuth server error ({provider}): {exc}\n{tb}")
            return Response({'detail': f"OAuth Authentication Failed: {str(exc)}"}, status=500)
