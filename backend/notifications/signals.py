import logging
from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Notification)
def send_notification_email_on_creation(sender, instance, created, **kwargs):
    """
    Sends an email to the user's inbox whenever a Notification is created.
    """
    if created and instance.user and instance.user.email:
        try:
            subject = f"BudgetBuddy: {instance.title}"
            message = (
                f"Hello {instance.user.first_name or instance.user.username},\n\n"
                f"You have received a new notification on BudgetBuddy:\n\n"
                f"Title: {instance.title}\n"
                f"Type: {instance.notification_type}\n"
                f"Priority: {instance.priority}\n"
                f"Message:\n{instance.message}\n\n"
                f"Log in to your BudgetBuddy account to view details.\n\n"
                f"Best regards,\nBudgetBuddy Team"
            )
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'BudgetBuddy <no-reply@budgetbuddy.local>')
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[instance.user.email],
                fail_silently=False,
            )
            logger.info("Notification email sent to %s for notification '%s'", instance.user.email, instance.title)
        except Exception as e:
            logger.exception("Failed to send notification email to %s: %s", instance.user.email, e)
