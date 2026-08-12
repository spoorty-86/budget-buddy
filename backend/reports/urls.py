from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ReportViewSet, MonthlyFinancialReportView,
    ExpenseReportView, SavingsReportView,
    FinancialSummaryReportView, ExportReportView
)

router = DefaultRouter()
router.register('items', ReportViewSet, basename='report')

urlpatterns = [
    path('monthly/', MonthlyFinancialReportView.as_view(), name='monthly-financial-report'),
    path('financial/', MonthlyFinancialReportView.as_view(), name='financial-report'),
    path('expenses/', ExpenseReportView.as_view(), name='expense-report'),
    path('expense/', ExpenseReportView.as_view(), name='expense-report-alt'),
    path('savings/', SavingsReportView.as_view(), name='savings-report'),
    path('savings-report/', SavingsReportView.as_view(), name='savings-report-alt'),
    path('summary/', FinancialSummaryReportView.as_view(), name='financial-summary-report'),
    path('financial-summary/', FinancialSummaryReportView.as_view(), name='financial-summary-report-alt'),
    path('export/', ExportReportView.as_view(), name='export-report'),
    path('export-data/', ExportReportView.as_view(), name='export-report-alt'),
    path('saved/', include(router.urls)),
]
