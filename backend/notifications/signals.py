import sys
import logging
from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification

logger = logging.getLogger(__name__)

# Persistent thread pool for background email dispatch (prevents thread killing under Gunicorn)
email_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix='budgetbuddy_email')


def _send_email_async(email_obj, recipient_email, title):
    try:
        email_obj.send(fail_silently=False)
        logger.info("Notification email dispatched to Google Account email %s for '%s'", recipient_email, title)
    except Exception as e:
        logger.exception("Failed to dispatch notification email to %s: %s", recipient_email, e)


@receiver(post_save, sender=Notification)
def send_notification_email_on_creation(sender, instance, created, **kwargs):
    """
    Sends a rich HTML + Plain Text email notification directly to the user's Google Account / registered email
    whenever a Notification is created in BudgetBuddy.
    Runs asynchronously via ThreadPoolExecutor so web requests complete instantly in 0.001s.
    """
    if created and instance.user:
        recipient_email = (getattr(instance.user, 'email', '') or '').strip()
        if not recipient_email and hasattr(instance.user, 'profile'):
            recipient_email = (getattr(instance.user.profile, 'email', '') or '').strip()

        if not recipient_email:
            logger.warning("Notification '%s' created for user %s, but user has no email address associated.", instance.title, instance.user.username)
            return

        try:
            user_display_name = instance.user.first_name or instance.user.username or 'BudgetBuddy User'
            login_url = "https://budget-buddy-apps.vercel.app/login"
            subject = f"BudgetBuddy Alert: {instance.title}"
            
            text_message = (
                f"Hello {user_display_name},\n\n"
                f"You have received a new notification in BudgetBuddy:\n\n"
                f"📌 Title: {instance.title}\n"
                f"🏷️ Type: {instance.notification_type}\n"
                f"⚡ Priority: {instance.priority}\n\n"
                f"💬 Message:\n{instance.message}\n\n"
                f"🔗 View in BudgetBuddy: {login_url}\n\n"
                f"Best regards,\n"
                f"BudgetBuddy Support Team"
            )

            type_color = "#10b981" if instance.notification_type == "SUCCESS" else (
                "#ef4444" if instance.notification_type == "ERROR" else (
                    "#f59e0b" if instance.notification_type == "WARNING" else "#3b82f6"
                )
            )

            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
              <meta charset="utf-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
              <title>{subject}</title>
            </head>
            <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; color: #1e293b;">
              <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);">
                <!-- Header -->
                <tr>
                  <td style="background-color: #0f172a; padding: 24px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 700; letter-spacing: -0.5px;">
                      Budget<span style="color: #10b981;">Buddy</span>
                    </h1>
                    <p style="color: #94a3b8; margin: 4px 0 0 0; font-size: 13px;">Google Account Mobile Email Alert</p>
                  </td>
                </tr>

                <!-- Content -->
                <tr>
                  <td style="padding: 32px 24px;">
                    <p style="font-size: 16px; margin-top: 0; color: #334155;">Hello <strong>{user_display_name}</strong>,</p>
                    <p style="font-size: 14px; color: #64748b; line-height: 1.5;">You have a new real-time notification on your BudgetBuddy account linked to <strong>{recipient_email}</strong>:</p>

                    <!-- Alert Box -->
                    <div style="background-color: #f8fafc; border-left: 4px solid {type_color}; padding: 16px; border-radius: 6px; margin: 20px 0;">
                      <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <span style="display: inline-block; background-color: {type_color}; color: #ffffff; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 12px; text-transform: uppercase; margin-right: 8px;">
                          {instance.notification_type}
                        </span>
                        <strong style="font-size: 16px; color: #0f172a;">{instance.title}</strong>
                      </div>
                      <p style="font-size: 14px; color: #334155; margin: 8px 0 0 0; line-height: 1.5; white-space: pre-wrap;">{instance.message}</p>
                    </div>

                    <!-- Call To Action Button -->
                    <div style="text-align: center; margin: 28px 0 12px 0;">
                      <a href="{login_url}" style="background-color: #10b981; color: #ffffff; padding: 12px 24px; text-decoration: none; font-size: 14px; font-weight: 600; border-radius: 8px; display: inline-block; box-shadow: 0 2px 4px rgba(16, 185, 129, 0.3);">
                        Open BudgetBuddy App &rarr;
                      </a>
                    </div>
                  </td>
                </tr>

                <!-- Footer -->
                <tr>
                  <td style="background-color: #f8fafc; padding: 16px 24px; text-align: center; border-top: 1px solid #e2e8f0;">
                    <p style="font-size: 12px; color: #94a3b8; margin: 0;">
                      This notification was sent to <strong>{recipient_email}</strong>.<br>
                      BudgetBuddy Platform &bull; <a href="{login_url}" style="color: #10b981; text-decoration: none;">https://budget-buddy-apps.vercel.app/login</a>
                    </p>
                  </td>
                </tr>
              </table>
            </body>
            </html>
            """

            from_email = 'BudgetBuddy <spoortiyadavcspoorthi@gmail.com>'
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=from_email,
                to=[recipient_email]
            )
            email.attach_alternative(html_message, "text/html")

            # In unit tests, run synchronously so mail.outbox works; in production, use ThreadPoolExecutor
            if 'test' in sys.argv or getattr(settings, 'EMAIL_BACKEND', '').endswith('locmem.EmailBackend'):
                _send_email_async(email, recipient_email, instance.title)
            else:
                email_executor.submit(_send_email_async, email, recipient_email, instance.title)

        except Exception as e:
            logger.exception("Failed to prepare notification email for %s: %s", getattr(instance.user, 'email', None), e)





