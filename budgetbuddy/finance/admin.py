from django.contrib import admin
from .models import Category, Income, Expense, Budget, SavingsGoal, Notification, Report
for m in [Category, Income, Expense, Budget, SavingsGoal, Notification, Report]:
    admin.site.register(m)
