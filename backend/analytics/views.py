from decimal import Decimal
from django.db.models import Sum
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from finance.models import Income, Expense, Budget, SavingsGoal
from notifications.models import Notification as UserNotification

MONTH_NAMES = [
    '', 'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]


def serialize_expense(exp):
    if not exp:
        return None
    return {
        'id': exp.id,
        'title': exp.title,
        'amount': str(exp.amount),
        'category': exp.category.name if exp.category else 'Uncategorized',
        'date_spent': exp.date_spent.isoformat() if hasattr(exp.date_spent, 'isoformat') else str(exp.date_spent),
        'notes': exp.notes or '',
    }


def get_financial_summary_dict(user):
    total_income = Income.objects.filter(user=user).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_expense = Expense.objects.filter(user=user).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    current_balance = total_income - total_expense

    total_savings = SavingsGoal.objects.filter(user=user).aggregate(total=Sum('saved_amount'))['total'] or Decimal('0.00')
    total_budget = Budget.objects.filter(user=user).aggregate(total=Sum('budget_amount'))['total'] or Decimal('0.00')
    remaining_budget = total_budget - total_expense

    return {
        'total_income': total_income,
        'total_expense': total_expense,
        'current_balance': current_balance,
        'total_savings': total_savings,
        'remaining_budget': remaining_budget,
        'Total Income': total_income,
        'Total Expense': total_expense,
        'Current Balance': current_balance,
        'Total Savings': total_savings,
        'Remaining Budget': remaining_budget,
    }


def get_category_analysis_dict(user):
    expenses = Expense.objects.filter(user=user)
    category_totals = (
        expenses.values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    result_dict = {}
    for item in category_totals:
        name = item['category__name'] or 'Uncategorized'
        amount = item['total'] or Decimal('0.00')
        result_dict[name] = amount
    return result_dict


def get_monthly_trend_dict(user):
    expenses = Expense.objects.filter(user=user)
    monthly_data = {}
    grouped = (
        expenses.values('date_spent__month')
        .annotate(total=Sum('amount'))
        .order_by('date_spent__month')
    )
    for item in grouped:
        m_num = item['date_spent__month']
        if m_num and 1 <= m_num <= 12:
            m_name = MONTH_NAMES[m_num]
            amount = item['total'] or Decimal('0.00')
            monthly_data[m_name] = amount
    return monthly_data


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def financial_summary(request):
    """
    Task 2 - Financial Summary API
    Returns:
      - Total Income
      - Total Expense
      - Current Balance = Total Income - Total Expense
      - Total Savings
      - Remaining Budget
    """
    user = request.user
    summary_data = get_financial_summary_dict(user)
    return Response(summary_data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def category_expense_analysis(request):
    """
    Task 3 - Category-wise Expense Analysis API
    Groups expenses by category and calculates total spending for each category.
    Example:
      Food -> 4500
      Shopping -> 7200
      Travel -> 1800
      Education -> 900
    """
    user = request.user
    expenses = Expense.objects.filter(user=user)

    category_totals = (
        expenses.values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    result_dict = {}
    result_list = []

    for item in category_totals:
        name = item['category__name'] or 'Uncategorized'
        amount = item['total'] or Decimal('0.00')
        result_dict[name] = amount
        result_list.append({
            'category': name,
            'category_name': name,
            'total_expense': amount,
            'total': amount,
        })

    fmt = (request.query_params.get('type') or request.query_params.get('as_list') or request.query_params.get('view') or request.query_params.get('format_type') or '').lower()
    if fmt in ('list', 'array', '1', 'true'):
        return Response(result_list)

    return Response(result_dict)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def monthly_expense_trend(request):
    """
    Task 4 - Monthly Expense Trend API
    Groups expenses month-wise.
    Example:
      January -> 8500
      February -> 7600
      March -> 9100
      April -> 6900
    """
    user = request.user
    expenses = Expense.objects.filter(user=user)

    monthly_data = {}
    monthly_list = []

    grouped = (
        expenses.values('date_spent__month')
        .annotate(total=Sum('amount'))
        .order_by('date_spent__month')
    )

    for item in grouped:
        m_num = item['date_spent__month']
        if m_num and 1 <= m_num <= 12:
            m_name = MONTH_NAMES[m_num]
            amount = item['total'] or Decimal('0.00')
            monthly_data[m_name] = amount
            monthly_list.append({
                'month': m_name,
                'month_name': m_name,
                'month_number': m_num,
                'total_expense': amount,
                'total': amount,
            })

    fmt = (request.query_params.get('type') or request.query_params.get('as_list') or request.query_params.get('view') or request.query_params.get('format_type') or '').lower()
    if fmt in ('list', 'array', '1', 'true'):
        return Response(monthly_list)

    return Response(monthly_data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def expense_extremes_analysis(request):
    """
    Task 5 - Highest & Lowest Expense API
    Returns:
      - Highest Expense
      - Lowest Expense
      - Latest Expense
      - Oldest Expense
    """
    user = request.user
    expenses = Expense.objects.filter(user=user)

    highest_exp = serialize_expense(expenses.order_by('-amount', '-date_spent').first())
    lowest_exp = serialize_expense(expenses.order_by('amount', 'date_spent').first())
    latest_exp = serialize_expense(expenses.order_by('-date_spent', '-created_at').first())
    oldest_exp = serialize_expense(expenses.order_by('date_spent', 'created_at').first())

    return Response({
        'highest_expense': highest_exp,
        'lowest_expense': lowest_exp,
        'latest_expense': latest_exp,
        'oldest_expense': oldest_exp,
        'Highest Expense': highest_exp,
        'Lowest Expense': lowest_exp,
        'Latest Expense': latest_exp,
        'Oldest Expense': oldest_exp,
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def unified_dashboard_api(request):
    """
    Task 6 - Dashboard API
    Combines everything into one Dashboard API response:
      - Financial Summary
      - Category-wise Analysis
      - Monthly Trend
      - Recent Transactions
      - Latest Notifications
      - Active Savings Goals
    """
    user = request.user

    # 1. Financial Summary
    fin_summary = get_financial_summary_dict(user)

    # 2. Category-wise Analysis
    cat_analysis = get_category_analysis_dict(user)
    expenses_by_cat = [
        {'category__name': cat, 'total': amt}
        for cat, amt in cat_analysis.items()
    ]

    # 3. Monthly Trend
    monthly_trend = get_monthly_trend_dict(user)

    # 4. Recent Transactions
    incomes = Income.objects.filter(user=user)
    expenses = Expense.objects.filter(user=user)

    recent_txs = []
    for inc in incomes.order_by('-income_date', '-created_at')[:5]:
        recent_txs.append({
            'id': f"inc-{inc.id}",
            'type': 'income',
            'title': inc.title,
            'amount': str(inc.amount),
            'date': inc.income_date.isoformat(),
        })
    for exp in expenses.order_by('-date_spent', '-created_at')[:5]:
        recent_txs.append({
            'id': f"exp-{exp.id}",
            'type': 'expense',
            'title': exp.title,
            'amount': str(exp.amount),
            'date': exp.date_spent.isoformat(),
            'category': exp.category.name if exp.category else 'Uncategorized',
        })
    recent_txs.sort(key=lambda item: item['date'], reverse=True)
    recent_txs = recent_txs[:5]

    # 5. Latest Notifications
    user_notifs = UserNotification.objects.filter(user=user).order_by('-created_at')[:5]
    latest_notifications = [
        {
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'notification_type': n.notification_type,
            'priority': n.priority,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat(),
        }
        for n in user_notifs
    ]

    # 6. Active Savings Goals
    goals = SavingsGoal.objects.filter(user=user)
    active_savings_goals = [
        {
            'id': g.id,
            'name': g.name,
            'target_amount': str(g.target_amount),
            'saved_amount': str(g.saved_amount),
            'target_date': g.target_date.isoformat() if g.target_date else None,
        }
        for g in goals
    ]

    # 7. Highest & Lowest Expenses
    highest_exp = serialize_expense(expenses.order_by('-amount', '-date_spent').first())
    lowest_exp = serialize_expense(expenses.order_by('amount', 'date_spent').first())
    latest_exp = serialize_expense(expenses.order_by('-date_spent', '-created_at').first())
    oldest_exp = serialize_expense(expenses.order_by('date_spent', 'created_at').first())
    expense_extremes = {
        'highest_expense': highest_exp,
        'lowest_expense': lowest_exp,
        'latest_expense': latest_exp,
        'oldest_expense': oldest_exp,
    }

    has_any_data = Income.objects.filter(user=user).exists() or Expense.objects.filter(user=user).exists()

    payload = {
        'financial_summary': fin_summary,
        'Financial Summary': fin_summary,

        'category_wise_analysis': cat_analysis,
        'Category-wise Analysis': cat_analysis,

        'monthly_trend': monthly_trend,
        'Monthly Trend': monthly_trend,

        'recent_transactions': recent_txs,
        'Recent Transactions': recent_txs,

        'latest_notifications': latest_notifications,
        'Latest Notifications': latest_notifications,

        'active_savings_goals': active_savings_goals,
        'Active Savings Goals': active_savings_goals,

        'expense_extremes': expense_extremes,
        'Highest & Lowest Expenses': expense_extremes,

        'total_income': str(fin_summary['total_income']),
        'total_expense': str(fin_summary['total_expense']),
        'current_balance': str(fin_summary['current_balance']),
        'total_savings': str(fin_summary['total_savings']),
        'total_budget': str(Budget.objects.filter(user=user).aggregate(total=Sum('budget_amount'))['total'] or Decimal('0.00')),
        'remaining_budget': str(fin_summary['remaining_budget']),
        'expenses_by_category': expenses_by_cat,
        'has_any_data': has_any_data,
    }

    return Response(payload)


