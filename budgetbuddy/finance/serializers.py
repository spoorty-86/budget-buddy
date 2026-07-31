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
        fields = ['id', 'source', 'amount', 'date_received', 'notes', 'created_at']
        read_only_fields = ['id', 'created_at']


class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Expense
        fields = ['id', 'title', 'amount', 'category', 'category_name', 'date_spent', 'notes', 'created_at']
        read_only_fields = ['id', 'created_at']


class BudgetSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    spent = serializers.SerializerMethodField()
    remaining = serializers.SerializerMethodField()
    usage_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Budget
        fields = ['id', 'category', 'category_name', 'monthly_limit', 'month', 'year', 'spent', 'remaining', 'usage_percentage']

    def get_spent(self, obj):
        total = Expense.objects.filter(
            user=obj.user, category=obj.category,
            date_spent__month=obj.month, date_spent__year=obj.year
        ).aggregate(total=Sum('amount'))['total']
        return total or 0

    def get_remaining(self, obj):
        spent = self.get_spent(obj)
        remaining = obj.monthly_limit - spent
        return remaining if remaining > 0 else 0

    def get_usage_percentage(self, obj):
        spent = self.get_spent(obj)
        if obj.monthly_limit and obj.monthly_limit > 0:
            return round((spent / obj.monthly_limit) * 100, 2)
        return 0


class SavingsGoalSerializer(serializers.ModelSerializer):
    goal_name = serializers.CharField(source='name', read_only=True)
    goal_status = serializers.CharField(source='status', read_only=True)
    remaining_amount = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = SavingsGoal
        fields = [
            'id', 'name', 'goal_name', 'target_amount', 'saved_amount', 'target_date',
            'status', 'goal_status', 'remaining_amount', 'progress_percentage',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'goal_name', 'goal_status', 'status', 'remaining_amount', 'progress_percentage',
            'created_at', 'updated_at',
        ]

    def get_remaining_amount(self, obj):
        return obj.remaining_amount

    def get_progress_percentage(self, obj):
        return obj.progress_percentage

    def validate_target_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Target amount must be greater than zero.')
        return value

    def validate_saved_amount(self, value):
        if value < 0:
            raise serializers.ValidationError('Saved amount cannot be negative.')
        return value

    def validate_target_date(self, value):
        from django.utils import timezone

        if value and self.instance is None and value < timezone.localdate():
            raise serializers.ValidationError('Target date cannot be in the past when creating a new goal.')
        return value

    def validate(self, attrs):
        target_amount = attrs.get('target_amount', getattr(self.instance, 'target_amount', None))
        saved_amount = attrs.get('saved_amount', getattr(self.instance, 'saved_amount', 0))
        if target_amount is not None and saved_amount is not None and saved_amount > target_amount:
            raise serializers.ValidationError('Saved amount cannot exceed the target amount.')
        return attrs


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'notification_type', 'priority', 'is_read', 'created_at']
        read_only_fields = ['id', 'created_at']


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'title', 'period_start', 'period_end', 'summary_json', 'created_at']
