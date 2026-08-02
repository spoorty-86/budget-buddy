from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    """Milestone 2 - expense categorization"""
    name = models.CharField(max_length=80, unique=True)
    icon = models.CharField(max_length=40, blank=True, default='tag')

    def __str__(self):
        return self.name


class Income(models.Model):
    """Milestone 1 schema / Milestone 2 - income management"""
    SOURCE_CHOICES = [
        ('SALARY', 'Salary'),
        ('POCKET_MONEY', 'Pocket Money'),
        ('SCHOLARSHIP', 'Scholarship'),
        ('FREELANCING', 'Freelancing'),
        ('BUSINESS', 'Business'),
        ('OTHER', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incomes')
    title = models.CharField(max_length=120)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    income_date = models.DateField()
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-income_date']

    def __str__(self):
        return f"{self.title}: {self.amount}"


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
    monthly_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    budget_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    month = models.PositiveSmallIntegerField()   # 1-12
    year = models.PositiveIntegerField()
    triggered_alerts = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'category', 'month', 'year')
        ordering = ['-year', '-month', '-created_at']

    def save(self, *args, **kwargs):
        if self.budget_amount and not self.monthly_limit:
            self.monthly_limit = self.budget_amount
        elif self.monthly_limit and not self.budget_amount:
            self.budget_amount = self.monthly_limit

        if self.pk:
            try:
                old = Budget.objects.get(pk=self.pk)
                if old.budget_amount != self.budget_amount or old.monthly_limit != self.monthly_limit:
                    self.triggered_alerts = []
            except Budget.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.category} budget {self.budget_amount} ({self.month}/{self.year})"


class SavingsGoal(models.Model):
    """Milestone 1 schema"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='savings_goals')
    name = models.CharField(max_length=120)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    saved_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    target_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name


class Notification(models.Model):
    """Milestone 1 schema"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.message[:40]


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
