from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Profile


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    full_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'full_name']

    def validate_username(self, value):
        """Ensure username is unique and not blank."""
        if not value.strip():
            raise serializers.ValidationError('Username cannot be empty.')
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('A user with this username already exists.')
        return value

    def validate_email(self, value):
        """Ensure email is unique."""
        if not value.strip():
            raise serializers.ValidationError('Email cannot be empty.')
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def validate_password(self, value):
        """Ensure password meets requirements."""
        if len(value.strip()) < 6:
            raise serializers.ValidationError('Password must be at least 6 characters long.')
        return value

    def create(self, validated_data):
        full_name = validated_data.pop('full_name', '')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        profile, _ = Profile.objects.get_or_create(user=user)
        if full_name:
            profile.full_name = full_name
            profile.save()
        return user


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', required=False)

    class Meta:
        model = Profile
        fields = ['id', 'username', 'email', 'full_name', 'currency', 'monthly_income_target', 'avatar', 'created_at']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        new_email = user_data.get('email')
        if new_email and instance.user:
            instance.user.email = new_email.strip()
            instance.user.save(update_fields=['email'])
        return super().update(instance, validated_data)


class PasswordResetSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    new_password = serializers.CharField(min_length=6)
    confirm_password = serializers.CharField(min_length=6)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return attrs


from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.db.models import Q


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom SimpleJWT serializer that allows logging in using either:
    - Username (case-insensitive)
    - Email address (case-insensitive)
    """
    def validate(self, attrs):
        login_id = attrs.get(self.username_field, '').strip()
        if login_id:
            user_obj = User.objects.filter(
                Q(username__iexact=login_id) | Q(email__iexact=login_id)
            ).first()
            if user_obj:
                attrs[self.username_field] = user_obj.username
        return super().validate(attrs)

