import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Notification)
def send_notification_email_on_creation(sender, instance, created, **kwargs):
    """
    Email notification dispatch disabled.
    In-app notifications remain fully functional in the dashboard.
    """
    if created and instance.user:
        logger.info("In-app notification created for user %s: '%s'", instance.user.username, instance.title)






