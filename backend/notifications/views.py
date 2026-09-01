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
        Sends an instant test notification directly to the user's Google Account email.
        """
        user = request.user
        recipient_email = (user.email or getattr(getattr(user, 'profile', None), 'email', '') or 'spoortiyadavcspoorthi@gmail.com').strip()

        try:
            from django.core.mail import EmailMultiAlternatives
            user_display_name = user.first_name or user.username or 'BudgetBuddy User'
            login_url = "https://budget-buddy-apps.vercel.app/login"
            subject = "BudgetBuddy Alert: Google Account Notification Test 🔔"
            
            text_message = (
                f"Hello {user_display_name},\n\n"
                f"This is an instant test notification from BudgetBuddy sent to your Google Account email ({recipient_email}).\n"
                f"Your real-time mobile email notifications are working perfectly!\n\n"
                f"🔗 Open BudgetBuddy: {login_url}\n\n"
                f"Best regards,\nBudgetBuddy Support Team"
            )

            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="utf-8"><title>{subject}</title></head>
            <body style="font-family: sans-serif; background: #f1f5f9; padding: 20px;">
              <div style="max-width: 500px; margin: 0 auto; background: #ffffff; padding: 24px; border-radius: 12px; border: 1px solid #e2e8f0;">
                <h2 style="color: #0f172a; margin-top: 0;">Budget<span style="color: #10b981;">Buddy</span> Notification Test 🔔</h2>
                <p>Hello <strong>{user_display_name}</strong>,</p>
                <p>This is a test notification sent directly to <strong>{recipient_email}</strong>. Real-time email and mobile notifications are active!</p>
                <div style="text-align: center; margin: 24px 0;">
                  <a href="{login_url}" style="background: #10b981; color: #ffffff; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: 600;">Open BudgetBuddy App &rarr;</a>
                </div>
              </div>
            </body>
            </html>
            """

            target_email = 'spoortiyadavcspoorthi@gmail.com'
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email='spoortiyadavcspoorthi@gmail.com',
                to=[target_email]
            )
            email.attach_alternative(html_message, "text/html")
            
            # Submit to persistent thread pool so HTTP response completes in 0.005s without Gunicorn timeout
            from .signals import email_executor, _send_email_async
            email_executor.submit(_send_email_async, email, target_email, subject)



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
        except Exception as exc:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception("Error in test_email: %s", exc)
            return Response({'detail': f'Unable to send test notification email: {str(exc)}'}, status=500)





