from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Budget, SavingsGoal
from notifications.models import Notification


@receiver(post_save, sender=Budget)
def budget_notification_handler(sender, instance, created, **kwargs):
    """Automatic notification creation for Budget Created & Budget Updated"""
    category_name = instance.category.name if instance.category else 'General'
    if created:
        Notification.objects.create(
            user=instance.user,
            title='Budget Created',
            message=f"Budget for '{category_name}' has been created for {instance.month}/{instance.year} with limit {instance.budget_amount}.",
            notification_type='SUCCESS',
            priority=1,
        )
    else:
        Notification.objects.create(
            user=instance.user,
            title='Budget Updated',
            message=f"Budget for '{category_name}' for {instance.month}/{instance.year} has been updated to {instance.budget_amount}.",
            notification_type='INFO',
            priority=0,
        )


@receiver(pre_save, sender=SavingsGoal)
def savings_goal_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = SavingsGoal.objects.get(pk=instance.pk)
            instance._was_completed = old_instance.saved_amount >= old_instance.target_amount
        except SavingsGoal.DoesNotExist:
            instance._was_completed = False
    else:
        instance._was_completed = False


@receiver(post_save, sender=SavingsGoal)
def savings_goal_notification_handler(sender, instance, created, **kwargs):
    """Automatic notification creation for Savings Goal Created & Savings Goal Completed"""
    if created:
        Notification.objects.create(
            user=instance.user,
            title='Savings Goal Created',
            message=f"Savings goal '{instance.name}' has been created with target {instance.target_amount}.",
            notification_type='SUCCESS',
            priority=1,
        )
        if instance.saved_amount >= instance.target_amount:
            Notification.objects.create(
                user=instance.user,
                title='Savings Goal Completed',
                message=f"Savings goal '{instance.name}' has been completed!",
                notification_type='SUCCESS',
                priority=2,
            )
    else:
        was_completed = getattr(instance, '_was_completed', False)
        is_completed = instance.saved_amount >= instance.target_amount
        if not was_completed and is_completed:
            Notification.objects.create(
                user=instance.user,
                title='Savings Goal Completed',
                message=f"Congratulations! Savings goal '{instance.name}' reached target of {instance.target_amount}.",
                notification_type='SUCCESS',
                priority=2,
            )
