from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail
import logging
from django.db.models import Sum
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from notifications.models import Notification as UserNotification
from .models import Category, Income, Expense, Budget, SavingsGoal, Notification as FinanceNotification, Report
from .serializers import (
    CategorySerializer, IncomeSerializer, ExpenseSerializer, BudgetSerializer,
    SavingsGoalSerializer, NotificationSerializer, ReportSerializer, BudgetAlertSerializer,
)


def create_user_notification(user, title, message, notification_type='SUCCESS', priority=0, send_email=False):
    UserNotification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        priority=priority,
    )

    logger = logging.getLogger(__name__)
    if send_email and user.email:
        try:
            send_mail(
                subject=f'BudgetBuddy: {title}',
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception:
            logger.exception('Failed to send user notification email for user id %s', getattr(user, 'id', None))


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class UserScopedViewSet(viewsets.ModelViewSet):
    """Base class: every user only sees/edits their own rows."""
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class IncomeViewSet(UserScopedViewSet):
    """Milestone 2 - income management functionality"""
    queryset = Income.objects.all()
    serializer_class = IncomeSerializer


class ExpenseViewSet(UserScopedViewSet):
    """Milestone 2 - expense tracking APIs + categorization"""
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer

    SORT_OPTIONS = {
        'latest': '-date_spent',
        'oldest': 'date_spent',
        'highest': '-amount',
        'lowest': 'amount',
    }

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        category = params.get('category')
        if category:
            if category.isdigit():
                queryset = queryset.filter(category_id=category)
            else:
                queryset = queryset.filter(category__name__iexact=category)

        sort = params.get('sort')
        if sort in self.SORT_OPTIONS:
            queryset = queryset.order_by(self.SORT_OPTIONS[sort])

        return queryset

    @action(detail=False, methods=['get'])
    def total(self, request):
        queryset = self.get_queryset()
        total_amount = queryset.aggregate(total=Sum('amount'))['total'] or 0
        return Response({'total': total_amount})


class BudgetViewSet(UserScopedViewSet):
    """Milestone 2 - budget creation system"""
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer

    @action(detail=False, methods=['get'], url_path='alerts', name='budget-alerts')
    def alerts(self, request):
        queryset = self.get_queryset()
        category = request.query_params.get('category')
        month = request.query_params.get('month')
        year = request.query_params.get('year')

        if category:
            if category.isdigit():
                queryset = queryset.filter(category_id=category)
            else:
                queryset = queryset.filter(category__name__iexact=category)
        if month:
            queryset = queryset.filter(month=int(month))
        if year:
            queryset = queryset.filter(year=int(year))

        serializer = BudgetAlertSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='summary', name='budget-summary')
    def summary(self, request):
        queryset = self.get_queryset()
        category = request.query_params.get('category')
        month = request.query_params.get('month')
        year = request.query_params.get('year')

        if category:
            if category.isdigit():
                queryset = queryset.filter(category_id=category)
            else:
                queryset = queryset.filter(category__name__iexact=category)
        if month:
            queryset = queryset.filter(month=int(month))
        if year:
            queryset = queryset.filter(year=int(year))

        budget = queryset.order_by('-year', '-month', '-created_at').first()
        if not budget:
            return Response({'detail': 'No budget found for the requested filters.'}, status=404)

        total_expense = Expense.objects.filter(
            user=request.user,
            category=budget.category,
            date_spent__month=budget.month,
            date_spent__year=budget.year,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        remaining_budget = budget.budget_amount - total_expense
        overspent_amount = max(total_expense - budget.budget_amount, Decimal('0.00'))

        def fmt(value):
            return f"{value:.2f}"

        return Response({
            'budget_amount': fmt(budget.budget_amount),
            'total_expense': fmt(total_expense),
            'remaining_budget': fmt(remaining_budget),
            'overspent_amount': fmt(overspent_amount),
        })


class BudgetAlertViewSet(UserScopedViewSet):
    """
    Task 5 - Create Budget Alert API protected by JWT Auth.
    """
    queryset = Budget.objects.all()
    serializer_class = BudgetAlertSerializer



class SavingsGoalViewSet(UserScopedViewSet):
    queryset = SavingsGoal.objects.all()
    serializer_class = SavingsGoalSerializer



class NotificationViewSet(UserScopedViewSet):
    queryset = FinanceNotification.objects.all()
    serializer_class = NotificationSerializer


class ReportViewSet(UserScopedViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard(request):
    """Milestone 2 - transaction dashboard.
    GET /api/finance/dashboard/?month=7&year=2026
    """
    user = request.user
    try:
        month = int(request.GET.get('month', 0))
    except (ValueError, TypeError):
        month = 0

    try:
        year = int(request.GET.get('year', 0))
    except (ValueError, TypeError):
        year = 0

    incomes = Income.objects.filter(user=user)
    expenses = Expense.objects.filter(user=user)
    budgets = Budget.objects.filter(user=user)

    if month > 0 and year > 0:
        incomes = incomes.filter(income_date__month=month, income_date__year=year)
        expenses = expenses.filter(date_spent__month=month, date_spent__year=year)
        budgets = budgets.filter(month=month, year=year)
    elif month > 0:
        incomes = incomes.filter(income_date__month=month)
        expenses = expenses.filter(date_spent__month=month)
        budgets = budgets.filter(month=month)
    elif year > 0:
        incomes = incomes.filter(income_date__year=year)
        expenses = expenses.filter(date_spent__year=year)
        budgets = budgets.filter(year=year)

    total_income = incomes.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_expense = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_budget = budgets.aggregate(total=Sum('budget_amount'))['total'] or Decimal('0.00')
    remaining_budget = total_budget - total_expense

    expenses_by_category = list(
        expenses.values('category__name')
                .annotate(total=Sum('amount'))
                .order_by('-total')
    )

    recent_transactions = []
    for income in incomes.order_by('-income_date', '-created_at')[:5]:
        recent_transactions.append({
            'id': f"inc-{income.id}",
            'type': 'income',
            'title': income.title,
            'amount': str(income.amount),
            'date': income.income_date.isoformat(),
        })
    for expense in expenses.order_by('-date_spent', '-created_at')[:5]:
        recent_transactions.append({
            'id': f"exp-{expense.id}",
            'type': 'expense',
            'title': expense.title,
            'amount': str(expense.amount),
            'date': expense.date_spent.isoformat(),
            'category': expense.category.name if expense.category else None,
        })

    recent_transactions.sort(key=lambda item: item['date'], reverse=True)
    recent_transactions = recent_transactions[:5]

    has_any_data = Income.objects.filter(user=user).exists() or Expense.objects.filter(user=user).exists()

    return Response({
        'total_income': str(total_income),
        'total_expense': str(total_expense),
        'current_balance': str(total_income - total_expense),
        'total_budget': str(total_budget),
        'remaining_budget': str(remaining_budget),
        'expenses_by_category': expenses_by_category,
        'recent_transactions': recent_transactions,
        'has_any_data': has_any_data,
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def summary(request):
    user = request.user
    total_income = Income.objects.filter(user=user).aggregate(total=Sum('amount'))['total'] or 0
    total_expense = Expense.objects.filter(user=user).aggregate(total=Sum('amount'))['total'] or 0
    return Response({
        'total_income': total_income,
        'total_expense': total_expense,
        'current_balance': total_income - total_expense,
    })
