from decimal import Decimal

from rest_framework import serializers
from django.db.models import Sum
from .models import Category, Income, Expense, Budget, SavingsGoal, Notification, Report


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'icon']


class IncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Income
        fields = ['id', 'title', 'source', 'amount', 'income_date', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Expense
        fields = ['id', 'title', 'amount', 'category', 'category_name', 'date_spent', 'notes', 'created_at']
        read_only_fields = ['id', 'created_at']


class BudgetSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    spent = serializers.SerializerMethodField()
    remaining_budget = serializers.SerializerMethodField()
    overspent_amount = serializers.SerializerMethodField()

    class Meta:
        model = Budget
        fields = ['id', 'category', 'category_name', 'budget_amount', 'monthly_limit', 'month', 'year', 'created_at', 'updated_at', 'spent', 'remaining_budget', 'overspent_amount']
        read_only_fields = ['id', 'created_at', 'updated_at', 'category_name', 'spent', 'remaining_budget', 'overspent_amount']

    def get_spent(self, obj):
        total = Expense.objects.filter(
            user=obj.user, category=obj.category,
            date_spent__month=obj.month, date_spent__year=obj.year
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        return total

    def get_remaining_budget(self, obj):
        return obj.budget_amount - self.get_spent(obj)

    def get_overspent_amount(self, obj):
        spent = self.get_spent(obj)
        return max(spent - obj.budget_amount, Decimal('0.00'))

    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user if request else None
        category = attrs.get('category')
        month = attrs.get('month')
        year = attrs.get('year')

        if user and category and month is not None and year is not None:
            queryset = Budget.objects.filter(user=user, category=category, month=month, year=year)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError({'non_field_errors': ['A budget for this category and month already exists.']})

        return attrs


class SavingsGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavingsGoal
        fields = ['id', 'name', 'target_amount', 'saved_amount', 'target_date']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'message', 'is_read', 'created_at']


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'title', 'period_start', 'period_end', 'summary_json', 'created_at']


class BudgetAlertSerializer(serializers.ModelSerializer):
    budget_category = serializers.SerializerMethodField()
    budget_amount = serializers.SerializerMethodField()
    total_expense = serializers.SerializerMethodField()
    budget_utilization_percentage = serializers.SerializerMethodField()
    alert_level = serializers.SerializerMethodField()
    alert_message = serializers.SerializerMethodField()

    class Meta:
        model = Budget
        fields = [
            'id', 'category', 'month', 'year',
            'budget_category', 'budget_amount', 'total_expense',
            'budget_utilization_percentage', 'alert_level', 'alert_message'
        ]

    def get_budget_category(self, obj):
        return obj.category.name if obj.category else 'General'

    def get_budget_amount(self, obj):
        return f"{obj.budget_amount:.2f}"

    def _get_calculations(self, obj):
        total_expense = Expense.objects.filter(
            user=obj.user, category=obj.category,
            date_spent__month=obj.month, date_spent__year=obj.year
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        budget_amt = obj.budget_amount or Decimal('0.00')
        if budget_amt > 0:
            utilization_pct = float((total_expense / budget_amt) * Decimal('100.0'))
        else:
            utilization_pct = 100.0 if total_expense > 0 else 0.0

        return total_expense, budget_amt, utilization_pct

    def get_total_expense(self, obj):
        total_expense, _, _ = self._get_calculations(obj)
        return f"{total_expense:.2f}"

    def get_budget_utilization_percentage(self, obj):
        _, _, utilization_pct = self._get_calculations(obj)
        return round(utilization_pct, 2)

    def get_alert_level(self, obj):
        _, _, utilization_pct = self._get_calculations(obj)
        if utilization_pct >= 100:
            return 'Budget Exceeded Alert'
        elif utilization_pct >= 90:
            return 'High Warning Alert'
        elif utilization_pct >= 80:
            return 'Warning Alert'
        return 'Normal'

    def get_alert_message(self, obj):
        _, _, utilization_pct = self._get_calculations(obj)
        cat_name = self.get_budget_category(obj)
        util_int = int(utilization_pct)
        if utilization_pct >= 100:
            return f"Your {cat_name} Budget has been exceeded."
        elif utilization_pct >= 80:
            return f"You have used {util_int}% of your monthly {cat_name} Budget."
        return f"You have used {util_int}% of your monthly {cat_name} Budget."

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['Budget Category'] = data['budget_category']
        data['Budget Amount'] = data['budget_amount']
        data['Total Expense'] = data['total_expense']
        data['Budget Utilization Percentage'] = data['budget_utilization_percentage']
        data['Alert Level'] = data['alert_level']
        data['Alert Message'] = data['alert_message']
        return data

