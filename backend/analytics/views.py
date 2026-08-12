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


def get_financial_summary_dict(user, month=0, year=0):
    inc_qs = Income.objects.filter(user=user)
    exp_qs = Expense.objects.filter(user=user)
    bud_qs = Budget.objects.filter(user=user)

    if year and year > 0:
        inc_qs = inc_qs.filter(income_date__year=year)
        exp_qs = exp_qs.filter(date_spent__year=year)
        bud_qs = bud_qs.filter(year=year)

    if month and month > 0:
        inc_qs = inc_qs.filter(income_date__month=month)
        exp_qs = exp_qs.filter(date_spent__month=month)
        bud_qs = bud_qs.filter(month=month)

    total_income = inc_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_expense = exp_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    current_balance = total_income - total_expense

    total_savings = SavingsGoal.objects.filter(user=user).aggregate(total=Sum('saved_amount'))['total'] or Decimal('0.00')

    # Calculate total budget and expenses strictly for configured budget categories
    total_budget = Decimal('0.00')
    budget_expenses_total = Decimal('0.00')
    category_variances = []

    for b in bud_qs:
        limit = b.budget_amount or b.monthly_limit or Decimal('0.00')
        total_budget += limit

        spent_for_b = Expense.objects.filter(
            user=user,
            category=b.category,
            date_spent__year=b.year,
            date_spent__month=b.month,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        budget_expenses_total += spent_for_b
        variance_for_b = limit - spent_for_b
        pct_used = float(round((spent_for_b / limit * 100), 1)) if limit > 0 else 0.0

        category_variances.append({
            'id': b.id,
            'category_id': b.category.id if b.category else None,
            'category_name': b.category.name if b.category else 'Uncategorized',
            'budget_limit': str(limit),
            'spent': str(spent_for_b),
            'variance': str(variance_for_b),
            'pct_used': pct_used,
            'status': 'OVER_BUDGET' if spent_for_b > limit else 'UNDER_BUDGET',
            'month': b.month,
            'year': b.year,
        })

    remaining_budget = total_budget - budget_expenses_total

    return {
        'total_income': total_income,
        'total_expense': total_expense,
        'current_balance': current_balance,
        'total_savings': total_savings,
        'total_budget': total_budget,
        'budget_expenses_total': budget_expenses_total,
        'remaining_budget': remaining_budget,
        'category_variances': category_variances,
        'Total Income': total_income,
        'Total Expense': total_expense,
        'Current Balance': current_balance,
        'Total Savings': total_savings,
        'Total Budget': total_budget,
        'Budget Expenses Total': budget_expenses_total,
        'Remaining Budget': remaining_budget,
        'Category Variances': category_variances,
    }


def get_category_analysis_dict(user, month=0, year=0):
    expenses = Expense.objects.filter(user=user)
    if year and year > 0:
        expenses = expenses.filter(date_spent__year=year)
    if month and month > 0:
        expenses = expenses.filter(date_spent__month=month)

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


def get_monthly_income_expense_trend(user, year=0):
    inc_qs = Income.objects.filter(user=user)
    exp_qs = Expense.objects.filter(user=user)
    if year and year > 0:
        inc_qs = inc_qs.filter(income_date__year=year)
        exp_qs = exp_qs.filter(date_spent__year=year)

    inc_grouped = inc_qs.values('income_date__month').annotate(total=Sum('amount'))
    exp_grouped = exp_qs.values('date_spent__month').annotate(total=Sum('amount'))

    inc_map = {item['income_date__month']: item['total'] for item in inc_grouped if item['income_date__month']}
    exp_map = {item['date_spent__month']: item['total'] for item in exp_grouped if item['date_spent__month']}

    trend = []
    for m_num in range(1, 13):
        m_name = MONTH_NAMES[m_num]
        inc_amt = inc_map.get(m_num, Decimal('0.00')) or Decimal('0.00')
        exp_amt = exp_map.get(m_num, Decimal('0.00')) or Decimal('0.00')
        trend.append({
            'month': m_name,
            'month_num': m_num,
            'income': str(inc_amt),
            'expense': str(exp_amt),
            'net': str(inc_amt - exp_amt)
        })
    return trend



@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def financial_summary(request):
    """
    Task 2 - Financial Summary API
    """
    user = request.user
    month = 0
    year = 0
    try:
        if request.query_params.get('month'):
            month = int(request.query_params.get('month'))
        if request.query_params.get('year'):
            year = int(request.query_params.get('year'))
    except (ValueError, TypeError):
        pass

    summary_data = get_financial_summary_dict(user, month=month, year=year)
    return Response(summary_data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def category_expense_analysis(request):
    """
    Task 3 - Category-wise Expense Analysis API
    """
    user = request.user
    month = 0
    year = 0
    try:
        if request.query_params.get('month'):
            month = int(request.query_params.get('month'))
        if request.query_params.get('year'):
            year = int(request.query_params.get('year'))
    except (ValueError, TypeError):
        pass

    cat_dict = get_category_analysis_dict(user, month=month, year=year)
    result_list = [
        {
            'category': name,
            'category_name': name,
            'total_expense': amt,
            'total': amt,
        }
        for name, amt in cat_dict.items()
    ]

    fmt = (request.query_params.get('type') or request.query_params.get('as_list') or request.query_params.get('view') or request.query_params.get('format_type') or '').lower()
    if fmt in ('list', 'array', '1', 'true'):
        return Response(result_list)

    return Response(cat_dict)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def monthly_expense_trend(request):
    """
    Task 4 - Monthly Expense Trend API
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
    Task 6 - Dashboard API (Filtered by month and year query params)
    """
    user = request.user

    month = 0
    year = 0
    try:
        if request.query_params.get('month'):
            month = int(request.query_params.get('month'))
        if request.query_params.get('year'):
            year = int(request.query_params.get('year'))
    except (ValueError, TypeError):
        pass

    # 1. Financial Summary
    fin_summary = get_financial_summary_dict(user, month=month, year=year)

    # 2. Category-wise Analysis
    cat_analysis = get_category_analysis_dict(user, month=month, year=year)
    expenses_by_cat = [
        {'category__name': cat, 'total': amt}
        for cat, amt in cat_analysis.items()
    ]

    # 3. Monthly Trend & Comparison
    monthly_trend = get_monthly_trend_dict(user)
    monthly_comparison = get_monthly_income_expense_trend(user, year=year)

    # 4. Filtered Recent Transactions
    incomes = Income.objects.filter(user=user)
    expenses = Expense.objects.filter(user=user)

    if year and year > 0:
        incomes = incomes.filter(income_date__year=year)
        expenses = expenses.filter(date_spent__year=year)
    if month and month > 0:
        incomes = incomes.filter(income_date__month=month)
        expenses = expenses.filter(date_spent__month=month)

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

    # 7. Highest & Lowest Expenses for period
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
        'monthly_comparison': monthly_comparison,
        'Monthly Comparison': monthly_comparison,

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
        'total_budget': str(fin_summary['total_budget']),
        'budget_expenses_total': str(fin_summary['budget_expenses_total']),
        'remaining_budget': str(fin_summary['remaining_budget']),
        'category_variances': fin_summary['category_variances'],
        'budget_variances': fin_summary['category_variances'],
        'expenses_by_category': expenses_by_cat,
        'has_any_data': has_any_data,
        'month': month,
        'year': year,
    }

    return Response(payload)


