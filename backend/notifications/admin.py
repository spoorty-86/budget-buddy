from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'priority', 'is_read', 'user', 'created_at')
    list_filter = ('notification_type', 'is_read', 'priority')
    search_fields = ('title', 'message', 'user__username')
