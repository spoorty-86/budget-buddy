from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    """Milestone 2 - expense categorization"""
    name = models.CharField(max_length=80, unique=True)
    icon = models.CharField(max_length=40, blank=True, default='tag')

    def save(self, *args, **kwargs):
        self.name = self.name.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Income(models.Model):
    """Milestone 1 schema / Milestone 2 - income management"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incomes')
    source = models.CharField(max_length=120)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date_received = models.DateField()
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_received']

    def __str__(self):
        return f"{self.source}: {self.amount}"


class Expense(models.Model):
    """Milestone 1 schema / Milestone 2 - expense tracking"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='expenses')
    title = models.CharField(max_length=120)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date_spent = models.DateField()
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_spent']

    def __str__(self):
        return f"{self.title}: {self.amount}"


class Budget(models.Model):
    """Milestone 2 - budget creation system"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budgets')
    monthly_limit = models.DecimalField(max_digits=12, decimal_places=2)
    month = models.PositiveSmallIntegerField()   # 1-12
    year = models.PositiveIntegerField()

    class Meta:
        unique_together = ('user', 'category', 'month', 'year')

    def __str__(self):
        return f"{self.category} limit {self.monthly_limit} ({self.month}/{self.year})"


class SavingsGoal(models.Model):
    """Milestone 1 schema"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='savings_goals')
    name = models.CharField(max_length=120)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    saved_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    target_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        from django.core.exceptions import ValidationError
        from django.utils import timezone

        errors = {}
        if self.target_amount <= 0:
            errors['target_amount'] = 'Target amount must be greater than zero.'
        if self.saved_amount < 0:
            errors['saved_amount'] = 'Saved amount cannot be negative.'
        if self.target_date and self._state.adding and self.target_date < timezone.localdate():
            errors['target_date'] = 'Target date cannot be in the past when creating a new goal.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        from django.utils import timezone

        self.full_clean()
        if self.target_amount > 0 and self.saved_amount >= self.target_amount:
            self.status = 'completed'
            self.saved_amount = min(self.saved_amount, self.target_amount)
        elif self.target_date and self.target_date < timezone.localdate():
            self.status = 'expired'
        else:
            self.status = 'active'
        super().save(*args, **kwargs)

    @property
    def remaining_amount(self):
        remaining = self.target_amount - self.saved_amount
        return remaining if remaining > 0 else 0

    @property
    def progress_percentage(self):
        if self.target_amount and self.target_amount > 0:
            return round((self.saved_amount / self.target_amount) * 100, 2)
        return 0

    def __str__(self):
        return f"{self.name} ({self.status})"


class Notification(models.Model):
    """Milestone 1 schema"""
    NOTIFICATION_TYPE_CHOICES = [
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('SUCCESS', 'Success'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=150)
    message = models.CharField(max_length=255)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES, default='INFO')
    priority = models.PositiveSmallIntegerField(default=0)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.notification_type})"


class Report(models.Model):
    """Milestone 1 schema - saved/generated reports"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    title = models.CharField(max_length=150)
    period_start = models.DateField()
    period_end = models.DateField()
    summary_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
