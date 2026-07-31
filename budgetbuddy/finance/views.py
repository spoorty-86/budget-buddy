from django.db.models import Sum
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from .models import Category, Income, Expense, Budget, SavingsGoal, Notification, Report
from .serializers import (
    CategorySerializer, IncomeSerializer, ExpenseSerializer, BudgetSerializer,
    SavingsGoalSerializer, NotificationSerializer, ReportSerializer,
)


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
            if category.upper() == 'UNCATEGORIZED':
                queryset = queryset.filter(category__isnull=True)
            elif category.isdigit():
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
        user = request.user
        month = int(request.GET.get('month', 0)) or None
        year = int(request.GET.get('year', 0)) or None

        budgets = self.get_queryset()
        if month and year:
            budgets = budgets.filter(month=month, year=year)

        alerts = []
        for budget in budgets:
            spent = Expense.objects.filter(
                user=user, category=budget.category,
                date_spent__month=budget.month, date_spent__year=budget.year
            ).aggregate(total=Sum('amount'))['total'] or 0
            if spent >= budget.monthly_limit:
                alerts.append({
                    'category': budget.category.name,
                    'message': f'You have exceeded the budget for {budget.category.name} this period.',
                    'spent': spent,
                    'limit': budget.monthly_limit,
                    'status': 'over',
                })
            elif spent >= budget.monthly_limit * 0.8:
                alerts.append({
                    'category': budget.category.name,
                    'message': f'You are close to your budget limit for {budget.category.name}.',
                    'spent': spent,
                    'limit': budget.monthly_limit,
                    'status': 'warning',
                })
        return Response(alerts)


class SavingsGoalViewSet(UserScopedViewSet):
    queryset = SavingsGoal.objects.all()
    serializer_class = SavingsGoalSerializer

    def perform_create(self, serializer):
        goal = serializer.save(user=self.request.user)
        if goal.status == 'completed':
            Notification.objects.create(
                user=self.request.user,
                message=f"Savings goal '{goal.name}' is complete!"
            )
        elif goal.status == 'expired':
            Notification.objects.create(
                user=self.request.user,
                message=f"Savings goal '{goal.name}' has expired."
            )

    def perform_update(self, serializer):
        existing = self.get_object()
        previous_status = existing.status
        goal = serializer.save()
        if goal.status != previous_status:
            if goal.status == 'completed':
                Notification.objects.create(
                    user=self.request.user,
                    message=f"Savings goal '{goal.name}' is complete!"
                )
            elif goal.status == 'expired':
                Notification.objects.create(
                    user=self.request.user,
                    message=f"Savings goal '{goal.name}' has expired."
                )

    @action(detail=False, methods=['get'], url_path='progress', name='goal-progress')
    def progress(self, request):
        goals = self.get_queryset()
        data = [
            {
                'id': goal.id,
                'goal_name': goal.name,
                'target_amount': goal.target_amount,
                'saved_amount': goal.saved_amount,
                'remaining_amount': goal.remaining_amount,
                'progress_percentage': goal.progress_percentage,
                'goal_status': goal.status,
            }
            for goal in goals
        ]
        return Response(data)


class NotificationViewSet(UserScopedViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer


class ReportViewSet(UserScopedViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer

    @action(detail=False, methods=['post'], url_path='generate', name='generate-report')
    def generate(self, request):
        user = request.user
        title = request.data.get('title', 'Financial report')
        period_start = request.data.get('period_start')
        period_end = request.data.get('period_end')

        if not period_start or not period_end:
            return Response({'detail': 'period_start and period_end are required.'}, status=status.HTTP_400_BAD_REQUEST)

        incomes = Income.objects.filter(user=user, date_received__gte=period_start, date_received__lte=period_end)
        expenses = Expense.objects.filter(user=user, date_spent__gte=period_start, date_spent__lte=period_end)
        budgets = Budget.objects.filter(user=user)
        goals = SavingsGoal.objects.filter(user=user)

        summary = {
            'total_income': incomes.aggregate(total=Sum('amount'))['total'] or 0,
            'total_expense': expenses.aggregate(total=Sum('amount'))['total'] or 0,
            'net_savings': (incomes.aggregate(total=Sum('amount'))['total'] or 0) - (expenses.aggregate(total=Sum('amount'))['total'] or 0),
            'expenses_by_category': list(expenses.values('category__name').annotate(total=Sum('amount')).order_by('-total')),
            'budget_usage': [
                {
                    'category': budget.category.name,
                    'monthly_limit': budget.monthly_limit,
                    'spent': Expense.objects.filter(
                        user=user, category=budget.category,
                        date_spent__month=budget.month, date_spent__year=budget.year
                    ).aggregate(total=Sum('amount'))['total'] or 0,
                }
                for budget in budgets
            ],
            'savings_goals': [
                {
                    'name': goal.name,
                    'target_amount': goal.target_amount,
                    'saved_amount': goal.saved_amount,
                    'remaining_amount': goal.remaining_amount,
                    'progress_percentage': goal.progress_percentage,
                    'status': goal.status,
                }
                for goal in goals
            ],
        }

        report = Report.objects.create(
            user=user,
            title=title,
            period_start=period_start,
            period_end=period_end,
            summary_json=summary,
        )

        return Response(ReportSerializer(report).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard(request):
    """Milestone 2 - transaction dashboard.
    GET /api/finance/dashboard/?month=7&year=2026
    """
    user = request.user
    month = int(request.GET.get('month', 0)) or None
    year = int(request.GET.get('year', 0)) or None

    incomes = Income.objects.filter(user=user)
    expenses = Expense.objects.filter(user=user)
    if month and year:
        incomes = incomes.filter(date_received__month=month, date_received__year=year)
        expenses = expenses.filter(date_spent__month=month, date_spent__year=year)

    total_income = incomes.aggregate(total=Sum('amount'))['total'] or 0
    total_expense = expenses.aggregate(total=Sum('amount'))['total'] or 0

    by_category = list(
        expenses.values('category__name').annotate(total=Sum('amount')).order_by('-total')
    )

    return Response({
        'total_income': total_income,
        'total_expense': total_expense,
        'net_balance': total_income - total_expense,
        'expenses_by_category': by_category,
        'recent_transactions': ExpenseSerializer(expenses[:5], many=True).data,
    })
