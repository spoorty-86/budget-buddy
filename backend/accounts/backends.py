from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Custom authentication backend that allows authentication using either:
    1. Username (case-insensitive)
    2. Email address (case-insensitive)
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if not username or not password:
            return None

        # Clean the input username/email
        login_identifier = username.strip()

        # Find user matching username or email case-insensitively
        try:
            users = User.objects.filter(
                Q(username__iexact=login_identifier) | Q(email__iexact=login_identifier)
            )
            
            for user in users:
                if user.check_password(password) and self.user_can_authenticate(user):
                    return user
        except Exception:
            return None

        return None
