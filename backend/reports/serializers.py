from decimal import Decimal
from rest_framework import serializers
from .models import Report
from finance.models import Expense, SavingsGoal, Income, Budget
from notifications.models import Notification


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'title', 'period_start', 'period_end', 'summary_json', 'created_at', 'user']
        read_only_fields = ['id', 'created_at', 'user']


class MonthlyFinancialReportSerializer(serializers.Serializer):
    month = serializers.IntegerField()
    year = serializers.IntegerField()
    total_income = serializers.CharField()
    total_expense = serializers.CharField()
    current_balance = serializers.CharField()
    total_savings = serializers.CharField()
    remaining_budget = serializers.CharField()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['Total Income'] = data['total_income']
        data['Total Expense'] = data['total_expense']
        data['Current Balance'] = data['current_balance']
        data['Total Savings'] = data['total_savings']
        data['Remaining Budget'] = data['remaining_budget']
        return data


class ExpenseReportItemSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = Expense
        fields = ['id', 'title', 'amount', 'category', 'category_name', 'date_spent', 'notes']

    def get_category_name(self, obj):
        return obj.category.name if obj.category else 'General'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        desc = instance.notes or getattr(instance, 'description', '') or ''
        data['Expense Title'] = data['title']
        data['Amount'] = f"{instance.amount:.2f}"
        data['Category'] = data['category_name']
        data['Date'] = str(instance.date_spent)
        data['Description'] = desc
        data['notes'] = desc
        return data


class SavingsReportItemSerializer(serializers.ModelSerializer):
    remaining_amount = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = SavingsGoal
        fields = [
            'id', 'name', 'target_amount', 'saved_amount',
            'remaining_amount', 'progress_percentage', 'target_date'
        ]

    def get_remaining_amount(self, obj):
        rem = obj.target_amount - obj.saved_amount
        return f"{max(Decimal('0.00'), rem):.2f}"

    def get_progress_percentage(self, obj):
        if obj.target_amount > 0:
            pct = float((obj.saved_amount / obj.target_amount) * Decimal('100.0'))
            return round(min(100.0, max(0.0, pct)), 2)
        return 0.0

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['Goal Name'] = instance.name
        data['Target Amount'] = f"{instance.target_amount:.2f}"
        data['Saved Amount'] = f"{instance.saved_amount:.2f}"
        data['Remaining Amount'] = data['remaining_amount']
        data['Progress Percentage'] = data['progress_percentage']
        return data


class CombinedFinancialSummarySerializer(serializers.Serializer):
    financial_summary = serializers.DictField()
    expense_summary = serializers.DictField()
    income_summary = serializers.DictField()
    budget_summary = serializers.DictField()
    savings_summary = serializers.DictField()
    latest_notifications = serializers.ListField()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['Financial Summary'] = data['financial_summary']
        data['Expense Summary'] = data['expense_summary']
        data['Income Summary'] = data['income_summary']
        data['Budget Summary'] = data['budget_summary']
        data['Savings Summary'] = data['savings_summary']
        data['Latest Notifications'] = data['latest_notifications']
        return data
