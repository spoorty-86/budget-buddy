from django.urls import path
from .views import (
    RegisterView, MeView, PasswordResetView,
    CustomTokenObtainPairView, CustomTokenRefreshView,
    OAuthLoginView, OAuthUrlsView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),        # JWT login
    path('refresh/', CustomTokenRefreshView.as_view(), name='refresh'),
    path('me/', MeView.as_view(), name='me'),
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('oauth/', OAuthLoginView.as_view(), name='oauth_login'),
    path('oauth/urls/', OAuthUrlsView.as_view(), name='oauth_urls'),
]
