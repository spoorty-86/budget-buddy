from django.urls import path
from .views import (
    financial_summary,
    category_expense_analysis,
    monthly_expense_trend,
    expense_extremes_analysis,
    unified_dashboard_api,
)

urlpatterns = [
    # Task 2 routes
    path('summary/', financial_summary, name='analytics-summary'),
    path('financial-summary/', financial_summary, name='analytics-financial-summary'),

    # Task 3 routes
    path('category-expenses/', category_expense_analysis, name='analytics-category-expenses'),
    path('category-wise-expenses/', category_expense_analysis, name='analytics-category-wise-expenses'),
    path('category-analysis/', category_expense_analysis, name='analytics-category-analysis'),

    # Task 4 routes
    path('monthly-expenses/', monthly_expense_trend, name='analytics-monthly-expenses'),
    path('monthly-trend/', monthly_expense_trend, name='analytics-monthly-trend'),
    path('monthly-expense-trend/', monthly_expense_trend, name='analytics-monthly-expense-trend'),

    # Task 5 routes
    path('highest-lowest-expenses/', expense_extremes_analysis, name='analytics-highest-lowest-expenses'),
    path('expense-stats/', expense_extremes_analysis, name='analytics-expense-stats'),
    path('expense-extremes/', expense_extremes_analysis, name='analytics-expense-extremes'),

    # Task 6 routes
    path('dashboard/', unified_dashboard_api, name='analytics-dashboard'),
    path('dashboard-api/', unified_dashboard_api, name='analytics-dashboard-api'),
]
