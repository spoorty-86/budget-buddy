from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    """
    Task 4 & 5: CRUD APIs for Notifications with JWT Authentication & Mark as Read endpoint.
    - Create: POST /api/notifications/
    - List: GET /api/notifications/
    - Retrieve: GET /api/notifications/<id>/
    - Update: PUT/PATCH /api/notifications/<id>/
    - Delete: DELETE /api/notifications/<id>/
    - Mark as read: POST/PATCH /api/notifications/<id>/mark-read/ or /mark_as_read/
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post', 'patch'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'patch'], url_path='mark_as_read')
    def mark_as_read(self, request, pk=None):
        return self.mark_read(request, pk=pk)

    @action(detail=True, methods=['post', 'patch'], url_path='toggle-pin')
    def toggle_pin(self, request, pk=None):
        notification = self.get_object()
        notification.is_pinned = not notification.is_pinned
        notification.save(update_fields=['is_pinned'])
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='bulk-delete')
    def bulk_delete(self, request):
        ids = request.data.get('ids', [])
        if not isinstance(ids, list):
            return Response({'detail': 'Invalid ids payload'}, status=400)
        deleted_count, _ = self.get_queryset().filter(id__in=ids).delete()
        return Response({'status': 'deleted', 'count': deleted_count})

    @action(detail=False, methods=['post'], url_path='bulk-pin')
    def bulk_pin(self, request):
        ids = request.data.get('ids', [])
        pin = request.data.get('pin', True)
        if not isinstance(ids, list):
            return Response({'detail': 'Invalid ids payload'}, status=400)
        updated_count = self.get_queryset().filter(id__in=ids).update(is_pinned=bool(pin))
        return Response({'status': 'updated', 'count': updated_count})

    @action(detail=False, methods=['post'], url_path='test-email')
    def test_email(self, request):
        """
        Sends an instant test notification to the user's logged-in Google Account email.
        """
        user = request.user
        recipient_email = user.email.strip() if user.email else ''
        
        if not recipient_email:
            return Response({
                'detail': 'Your account does not have an email address associated with it. Please update your profile or sign in with your Google Account.'
            }, status=400)

        # Creating notification automatically triggers the post_save email signal
        notification = Notification.objects.create(
            user=user,
            title='Google Account Notification Test 🔔',
            message=f'This is a test notification from BudgetBuddy sent to your Google Account email ({recipient_email}). Your real-time email & mobile notifications are working perfectly!',
            notification_type='SUCCESS',
            priority=1,
        )

        serializer = self.get_serializer(notification)
        return Response({
            'detail': f'Test notification created and email dispatched to {recipient_email}!',
            'notification': serializer.data,
            'email': recipient_email,
        })

