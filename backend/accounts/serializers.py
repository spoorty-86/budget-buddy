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
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Profile
        fields = ['id', 'username', 'email', 'full_name', 'currency', 'monthly_income_target', 'avatar', 'created_at']


class PasswordResetSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    new_password = serializers.CharField(min_length=6)
    confirm_password = serializers.CharField(min_length=6)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return attrs
