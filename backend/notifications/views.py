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

    @action(detail=False, methods=['get'], url_path='smtp-diag')
    def smtp_diag(self, request):
        """
        Diagnostic endpoint: tests DNS resolution, TCP port connectivity across ports 587, 2525, and 465 directly from Render.
        """
        import socket
        import smtplib
        from django.conf import settings

        host = getattr(settings, 'EMAIL_HOST', 'smtp-relay.brevo.com')
        user = getattr(settings, 'EMAIL_HOST_USER', '')
        pwd = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', '')

        ports_to_test = [587, 2525, 465]
        port_results = {}

        dns_status = "UNKNOWN"
        try:
            ip = socket.gethostbyname(host)
            dns_status = f"PASS ({ip})"
        except Exception as e:
            dns_status = f"FAIL ({str(e)})"

        for p in ports_to_test:
            res = {'tcp': 'UNKNOWN', 'auth': 'UNKNOWN'}
            try:
                sock = socket.create_connection((host, p), timeout=5)
                sock.close()
                res['tcp'] = "PASS"
            except Exception as e:
                res['tcp'] = f"FAIL ({str(e)})"

            if res['tcp'] == "PASS":
                try:
                    if p == 465:
                        server = smtplib.SMTP_SSL(host, p, timeout=5)
                    else:
                        server = smtplib.SMTP(host, p, timeout=5)
                        server.starttls()

                    if user and pwd:
                        server.login(user, pwd)
                    server.quit()
                    res['auth'] = "PASS"
                except Exception as e:
                    res['auth'] = f"FAIL ({e.__class__.__name__}: {str(e)})"
            port_results[str(p)] = res

        working_ports = [p for p, r in port_results.items() if r.get('auth') == 'PASS']

        diag = {
            'EMAIL_HOST': host,
            'EMAIL_HOST_USER': user,
            'DEFAULT_FROM_EMAIL': from_email,
            'dns_resolution': dns_status,
            'port_results': port_results,
            'working_ports': working_ports,
            'overall_status': 'PASS' if working_ports else 'FAIL',
        }
        status_code = 200 if working_ports else 500
        return Response(diag, status=status_code)

    @action(detail=False, methods=['post'], url_path='test-email')
    def test_email(self, request):
        """
        Sends an instant test notification directly to the authenticated user's registered email address.
        """
        import logging
        from django.conf import settings
        from django.core.mail import EmailMultiAlternatives, get_connection

        logger = logging.getLogger(__name__)

        user = request.user
        if not user.is_authenticated:
            return Response({'success': False, 'detail': 'Authentication required.'}, status=401)

        recipient_email = (getattr(user, 'email', '') or '').strip()
        if not recipient_email and hasattr(user, 'profile'):
            recipient_email = (getattr(user.profile, 'email', '') or '').strip()

        if not recipient_email:
            return Response(
                {'success': False, 'detail': 'Your account does not have a registered email address. Please update your profile with a valid email in Profile settings.'},
                status=400
            )

        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'BudgetBuddy Support <spoortiyadavcspoorthi@gmail.com>')
        logger.info("TEST EMAIL REQUEST user_id=%s, username=%s, recipient=%s, sender=%s", user.id, user.username, recipient_email, from_email)

        try:
            # 1. Create in-app Notification record in DB for history
            notification = Notification.objects.create(
                user=user,
                title='Account Notification Test',
                message=f'This is a test notification from BudgetBuddy sent to your registered email ({recipient_email}). Your real-time email notifications are working perfectly!',
                notification_type='SUCCESS',
                priority=1,
            )

            user_display_name = user.first_name or user.username or 'BudgetBuddy User'
            login_url = "https://budget-buddy-apps.vercel.app/login"
            subject = "BudgetBuddy Alert: Account Notification Test"

            text_message = (
                f"Hello {user_display_name},\n\n"
                f"This is a test notification from BudgetBuddy sent to your registered email ({recipient_email}).\n\n"
                f"Your real-time email notifications are working perfectly!\n\n"
                f"🔗 Open BudgetBuddy: {login_url}\n\n"
                f"Best regards,\nBudgetBuddy Support Team"
            )

            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="utf-8"><title>{subject}</title></head>
            <body style="font-family: sans-serif; background-color: #f1f5f9; padding: 20px;">
              <div style="max-width: 600px; margin: 0 auto; background: #ffffff; padding: 24px; border-radius: 12px;">
                <h1 style="color: #0f172a; margin: 0;">Budget<span style="color: #10b981;">Buddy</span></h1>
                <p style="color: #64748b;">Hello <strong>{user_display_name}</strong>,</p>
                <p>This is a test notification sent to your registered email address <strong>{recipient_email}</strong>.</p>
                <div style="background-color: #f8fafc; border-left: 4px solid #10b981; padding: 16px; margin: 20px 0;">
                  <strong style="color: #0f172a;">Account Notification Test</strong>
                  <p style="margin: 4px 0 0 0; color: #334155;">Your real-time email notifications are working perfectly!</p>
                </div>
                <a href="{login_url}" style="background-color: #10b981; color: #ffffff; padding: 10px 20px; text-decoration: none; border-radius: 6px; display: inline-block;">Open BudgetBuddy App &rarr;</a>
              </div>
            </body>
            </html>
            """

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=from_email,
                to=[recipient_email],
            )
            email.attach_alternative(html_message, "text/html")

            logger.info("EMAIL SEND START")
            sent_count = 0
            last_error = None

            # Always try port 2525 first since smtp-diag proves port 2525 is open & authenticated on Render
            ordered_ports = [2525, 587, 465]

            for p in ordered_ports:
                use_ssl = (p == 465)
                use_tls = not use_ssl
                try:
                    conn = get_connection(
                        backend='django.core.mail.backends.smtp.EmailBackend',
                        host=getattr(settings, 'EMAIL_HOST', 'smtp-relay.brevo.com'),
                        port=p,
                        username=getattr(settings, 'EMAIL_HOST_USER', ''),
                        password=getattr(settings, 'EMAIL_HOST_PASSWORD', ''),
                        use_ssl=use_ssl,
                        use_tls=use_tls,
                        timeout=5,
                        fail_silently=False
                    )
                    email.connection = conn
                    sent_count = email.send(fail_silently=False)
                    if sent_count >= 1:
                        logger.info("SMTP send SUCCESS on port %s!", p)
                        break
                except Exception as port_exc:
                    last_error = port_exc
                    logger.warning("SMTP send failed on port %s: %s - %s", p, port_exc.__class__.__name__, str(port_exc))

            if sent_count < 1:
                if last_error:
                    raise last_error
                return Response({'success': False, 'detail': 'Test email dispatch returned 0 sent messages.'}, status=500)

            logger.info("EMAIL SEND SUCCESS smtp_result=%s, recipient=%s", sent_count, recipient_email)
            notification_data = {
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'notification_type': notification.notification_type,
                'priority': notification.priority,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat() if hasattr(notification.created_at, 'isoformat') else str(notification.created_at),
            }
            return Response({
                'success': True,
                'detail': f'Test email accepted by SMTP server and dispatched to {recipient_email}!',
                'recipient': recipient_email,
                'notification': notification_data,
            })
        except Exception as exc:
            logger.exception("EMAIL SEND FAILURE user_id=%s, recipient=%s: %s", getattr(user, 'id', None), recipient_email, str(exc))
            return Response({'success': False, 'detail': f'Test email sending failed: {exc.__class__.__name__} - {str(exc)}'}, status=500)








