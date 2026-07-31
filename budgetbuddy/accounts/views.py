from rest_framework import generics, permissions
from rest_framework.response import Response
from .models import Profile
from .serializers import RegisterSerializer, ProfileSerializer


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/  -- Milestone 1: user registration"""
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer


class MeView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/auth/me/  -- current user's profile"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user.profile


