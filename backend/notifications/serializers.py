from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'notification_type', 'priority', 'is_read', 'is_pinned', 'created_at', 'user']
        read_only_fields = ['id', 'created_at', 'user']
