from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, IncomeViewSet, ExpenseViewSet, BudgetViewSet,
    SavingsGoalViewSet, NotificationViewSet, ReportViewSet, dashboard, summary,
)

router = DefaultRouter()
router.register('categories', CategoryViewSet)
router.register('incomes', IncomeViewSet, basename='income')
router.register('expenses', ExpenseViewSet, basename='expense')
router.register('budgets', BudgetViewSet, basename='budget')
router.register('savings-goals', SavingsGoalViewSet, basename='savingsgoal')
router.register('notifications', NotificationViewSet, basename='notification')
router.register('reports', ReportViewSet, basename='report')

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
    path('summary/', summary, name='summary'),
    path('', include(router.urls)),
]
