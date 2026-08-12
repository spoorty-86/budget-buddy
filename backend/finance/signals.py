from decimal import Decimal
from django.db.models import Sum
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import Budget, SavingsGoal, Expense, Income
from notifications.models import Notification


def calculate_budget_utilization(budget):
    """
    Task 1: Calculate current budget utilization percentage
    Formula: Budget Utilization = (Total Expense / Budget Amount) * 100
    """
    total_expense = Expense.objects.filter(
        user=budget.user,
        category=budget.category,
        date_spent__month=budget.month,
        date_spent__year=budget.year,
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    budget_amt = budget.budget_amount or budget.monthly_limit or Decimal('0.00')
    if budget_amt > 0:
        utilization_pct = float((total_expense / budget_amt) * Decimal('100.0'))
    else:
        utilization_pct = 100.0 if total_expense > 0 else 0.0

    return total_expense, budget_amt, utilization_pct


def check_and_trigger_budget_alerts(budget):
    """
    Tasks 1, 2, 3 & 4:
    - Calculates utilization percentage
    - Generates warning alerts (80% Warning Alert, 90% High Warning Alert, 100%+ Budget Exceeded Alert)
    - Prevents duplicate alerts unless budget is reset or new period starts
    - Connects Budget module with Notification module
    """
    if not budget or not budget.category:
        return

    total_expense, budget_amt, utilization_pct = calculate_budget_utilization(budget)
    category_name = budget.category.name
    util_int = int(utilization_pct)

    if budget_amt <= 0:
        return

    triggered = list(budget.triggered_alerts or [])
    updated_triggered = list(triggered)

    if utilization_pct >= 100:
        if '100' not in updated_triggered:
            Notification.objects.create(
                user=budget.user,
                title='Budget Exceeded Alert',
                message=f"Your {category_name} Budget has been exceeded.",
                notification_type='ERROR',
                priority=3,
            )
            if '80' not in updated_triggered:
                updated_triggered.append('80')
            if '90' not in updated_triggered:
                updated_triggered.append('90')
            updated_triggered.append('100')
    elif utilization_pct >= 90:
        if '90' not in updated_triggered:
            Notification.objects.create(
                user=budget.user,
                title='High Warning Alert',
                message=f"You have used {util_int}% of your monthly {category_name} Budget.",
                notification_type='WARNING',
                priority=2,
            )
            if '80' not in updated_triggered:
                updated_triggered.append('80')
            updated_triggered.append('90')
        if '100' in updated_triggered:
            updated_triggered.remove('100')
    elif utilization_pct >= 80:
        if '80' not in updated_triggered:
            Notification.objects.create(
                user=budget.user,
                title='Warning Alert',
                message=f"You have used {util_int}% of your monthly {category_name} Budget.",
                notification_type='WARNING',
                priority=1,
            )
            updated_triggered.append('80')
        if '90' in updated_triggered:
            updated_triggered.remove('90')
        if '100' in updated_triggered:
            updated_triggered.remove('100')
    else:
        for val in ['80', '90', '100']:
            if val in updated_triggered:
                updated_triggered.remove(val)

    if updated_triggered != triggered:
        budget.triggered_alerts = updated_triggered
        budget.save(update_fields=['triggered_alerts'])


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
    check_and_trigger_budget_alerts(instance)


import re
import datetime

def get_month_year(date_val):
    if not date_val:
        return None, None
    if isinstance(date_val, (datetime.date, datetime.datetime)):
        return date_val.month, date_val.year
    if isinstance(date_val, str):
        match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_val)
        if match:
            return int(match.group(2)), int(match.group(1))
        try:
            d = datetime.date.fromisoformat(date_val.split('T')[0])
            return d.month, d.year
        except Exception:
            pass
    return getattr(date_val, 'month', None), getattr(date_val, 'year', None)


@receiver(pre_save, sender=Expense)
def expense_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_expense = Expense.objects.get(pk=instance.pk)
            instance._old_category = old_expense.category
            old_m, old_y = get_month_year(old_expense.date_spent)
            instance._old_month = old_m
            instance._old_year = old_y
        except Expense.DoesNotExist:
            pass


@receiver(post_save, sender=Expense)
def expense_post_save_budget_alert(sender, instance, created, **kwargs):
    """Run budget alert logic whenever a new expense is added or an existing expense is updated."""
    if created:
        cat_name = instance.category.name if instance.category else 'General'
        Notification.objects.create(
            user=instance.user,
            title='Expense Added',
            message=f"Expense '{instance.title}' of ₹{instance.amount:,.2f} for '{cat_name}' has been added.",
            notification_type='INFO',
            priority=1,
        )

    month, year = get_month_year(instance.date_spent)
    if month and year:
        total_inc = Income.objects.filter(
            user=instance.user,
            income_date__month=month,
            income_date__year=year
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        total_exp_month = Expense.objects.filter(
            user=instance.user,
            date_spent__month=month,
            date_spent__year=year
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        if total_inc > 0:
            if total_exp_month > total_inc:
                if not Notification.objects.filter(user=instance.user, title='High Alert', message__icontains=f"income for {month}/{year}").exists():
                    Notification.objects.create(
                        user=instance.user,
                        title='High Alert',
                        message=f"High Warning Alert: Total expenses (₹{total_exp_month:,.2f}) have exceeded your total income (₹{total_inc:,.2f}) for {month}/{year}.",
                        notification_type='ERROR',
                        priority=3,
                    )
            elif total_exp_month >= total_inc * Decimal('0.8'):
                if not Notification.objects.filter(user=instance.user, title='Warning Alert', message__icontains=f"income for {month}/{year}").exists():
                    pct = int((total_exp_month / total_inc) * Decimal('100.0'))
                    Notification.objects.create(
                        user=instance.user,
                        title='Warning Alert',
                        message=f"Warning Alert: You have spent {pct}% of your monthly income for {month}/{year}.",
                        notification_type='WARNING',
                        priority=2,
                    )

    if instance.category and month and year:
        budgets = list(Budget.objects.filter(
            user=instance.user,
            category=instance.category,
            month=month,
            year=year,
        ))
        if not budgets:
            budgets = list(Budget.objects.filter(
                user=instance.user,
                category=instance.category,
            ))
        for b in budgets:
            check_and_trigger_budget_alerts(b)

    old_cat = getattr(instance, '_old_category', None)
    old_m = getattr(instance, '_old_month', None)
    old_y = getattr(instance, '_old_year', None)
    if old_cat and old_m and old_y and (old_cat != instance.category or old_m != month or old_y != year):
        old_budgets = Budget.objects.filter(
            user=instance.user,
            category=old_cat,
            month=old_m,
            year=old_y,
        )
        for b in old_budgets:
            check_and_trigger_budget_alerts(b)


@receiver(post_delete, sender=Expense)
def expense_post_delete_budget_alert(sender, instance, **kwargs):
    """Run budget alert logic whenever an expense is deleted."""
    month, year = get_month_year(instance.date_spent)
    if instance.category and month and year:
        budgets = Budget.objects.filter(
            user=instance.user,
            category=instance.category,
            month=month,
            year=year,
        )
        for b in budgets:
            check_and_trigger_budget_alerts(b)


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
