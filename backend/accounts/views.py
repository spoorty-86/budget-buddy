from django.contrib.auth import get_user_model
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Profile
from .serializers import RegisterSerializer, ProfileSerializer, PasswordResetSerializer
from notifications.models import Notification as UserNotification

User = get_user_model()


import logging
import traceback

logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/  -- Milestone 1: user registration"""
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except Exception as exc:
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


class PasswordResetView(APIView):
    """POST /api/auth/password-reset/  -- reset password by username and email"""
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
