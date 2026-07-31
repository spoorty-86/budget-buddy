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
