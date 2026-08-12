from decimal import Decimal
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from finance.models import Category, Income, Expense, Budget, SavingsGoal
from notifications.models import Notification
from reports.models import Report

User = get_user_model()


class ReportsTasksTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='reportuser', password='secret123')
        self.client.force_authenticate(user=self.user)

        self.food, _ = Category.objects.get_or_create(name='Food', defaults={'icon': 'utensils'})
        self.travel, _ = Category.objects.get_or_create(name='Travel', defaults={'icon': 'plane'})

        # Setup financial records for 8/2026
        Income.objects.create(
            user=self.user,
            title='Monthly Salary',
            amount=Decimal('45000.00'),
            income_date='2026-08-01',
            source='SALARY'
        )

        Expense.objects.create(
            user=self.user,
            title='Groceries',
            amount=Decimal('5000.00'),
            date_spent='2026-08-04',
            category=self.food,
            notes='Weekly grocery spending'
        )

        Expense.objects.create(
            user=self.user,
            title='Flight Ticket',
            amount=Decimal('15000.00'),
            date_spent='2026-08-10',
            category=self.travel,
            notes='Vacation flight'
        )

        Budget.objects.create(
            user=self.user,
            category=self.food,
            budget_amount=Decimal('10000.00'),
            month=8,
            year=2026
        )

        SavingsGoal.objects.create(
            user=self.user,
            name='Emergency Fund',
            target_amount=Decimal('50000.00'),
            saved_amount=Decimal('12000.00')
        )

        Notification.objects.create(
            user=self.user,
            title='Welcome Alert',
            message='Welcome to BudgetBuddy reports!',
            notification_type='INFO'
        )

    def test_task_1_reports_app_registered(self):
        """Task 1: Verify reports app is registered in INSTALLED_APPS"""
        self.assertIn('reports', settings.INSTALLED_APPS)
        r = Report.objects.create(user=self.user, title='Test Report')
        self.assertEqual(r.title, 'Test Report')

    def test_task_2_monthly_financial_report_api(self):
        """
        Task 2: Monthly Financial Report API returns:
        - Total Income
        - Total Expense
        - Current Balance
        - Total Savings
        - Remaining Budget
        Protected by JWT Authentication.
        """
        url = reverse('monthly-financial-report') + '?month=8&year=2026'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['Total Income'], '45000.00')
        self.assertEqual(response.data['Total Expense'], '20000.00')
        self.assertEqual(response.data['Current Balance'], '25000.00')
        self.assertEqual(response.data['Total Savings'], '12000.00')

        # Test JWT protection
        self.client.logout()
        unauth_response = self.client.get(url)
        self.assertEqual(unauth_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_task_3_expense_report_api(self):
        """
        Task 3: Expense Report API returns all expenses in a date range with required fields:
        - Expense Title
        - Category
        - Amount
        - Date
        - Description
        Protected by JWT Authentication.
        """
        url = reverse('expense-report') + '?start_date=2026-08-01&end_date=2026-08-05'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        item = response.data['expenses'][0]

        self.assertEqual(item['Expense Title'], 'Groceries')
        self.assertEqual(item['Category'], 'Food')
        self.assertEqual(item['Amount'], '5000.00')
        self.assertEqual(item['Date'], '2026-08-04')
        self.assertEqual(item['Description'], 'Weekly grocery spending')

        # Test JWT protection
        self.client.logout()
        unauth_response = self.client.get(url)
        self.assertEqual(unauth_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_task_4_savings_report_api(self):
        """
        Task 4: Savings Report API returns:
        - Goal Name
        - Target Amount
        - Saved Amount
        - Remaining Amount
        - Progress Percentage
        Protected by JWT Authentication.
        """
        url = reverse('savings-report')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        goal = response.data['goals'][0]

        self.assertEqual(goal['Goal Name'], 'Emergency Fund')
        self.assertEqual(goal['Target Amount'], '50000.00')
        self.assertEqual(goal['Saved Amount'], '12000.00')
        self.assertEqual(goal['Remaining Amount'], '38000.00')
        self.assertEqual(goal['Progress Percentage'], 24.0)

        # Test JWT protection
        self.client.logout()
        unauth_response = self.client.get(url)
        self.assertEqual(unauth_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_task_5_financial_summary_report_api(self):
        """
        Task 5: Financial Summary Report API combines everything:
        - Financial Summary
        - Expense Summary
        - Income Summary
        - Budget Summary
        - Savings Summary
        - Latest Notifications
        Protected by JWT Authentication.
        """
        url = reverse('financial-summary-report') + '?month=8&year=2026'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Financial Summary', response.data)
        self.assertIn('Expense Summary', response.data)
        self.assertIn('Income Summary', response.data)
        self.assertIn('Budget Summary', response.data)
        self.assertIn('Savings Summary', response.data)
        self.assertIn('Latest Notifications', response.data)

        # Test JWT protection
        self.client.logout()
        unauth_response = self.client.get(url)
        self.assertEqual(unauth_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_task_6_date_filters(self):
        """
        Task 6: Add Date Filters:
        - Current Month (period=current_month)
        - Previous Month (period=previous_month)
        - Custom Start & End Date
        """
        # Test custom dates
        url_custom = reverse('financial-summary-report') + '?start_date=2026-08-01&end_date=2026-08-31'
        res_custom = self.client.get(url_custom)
        self.assertEqual(res_custom.status_code, status.HTTP_200_OK)

        # Test period=current_month
        url_curr = reverse('financial-summary-report') + '?period=current_month'
        res_curr = self.client.get(url_curr)
        self.assertEqual(res_curr.status_code, status.HTTP_200_OK)

        # Test period=previous_month
        url_prev = reverse('financial-summary-report') + '?period=previous_month'
        res_prev = self.client.get(url_prev)
        self.assertEqual(res_prev.status_code, status.HTTP_200_OK)

    def test_task_7_export_ready_data(self):
        """
        Task 7: Prepare Export-Ready Data (CSV & JSON format)
        Protected by JWT Authentication.
        """
        # Test JSON format
        url_json = reverse('export-report') + '?report_type=expenses&format=json&start_date=2026-08-01&end_date=2026-08-31'
        res_json = self.client.get(url_json)
        self.assertEqual(res_json.status_code, status.HTTP_200_OK)
        self.assertIn('headers', res_json.data)
        self.assertIn('rows', res_json.data)
        self.assertIn('csv_download_url', res_json.data)

        # Test CSV format
        url_csv = reverse('export-report') + '?report_type=expenses&format=csv&start_date=2026-08-01&end_date=2026-08-31'
        res_csv = self.client.get(url_csv)
        self.assertEqual(res_csv.status_code, status.HTTP_200_OK)
        self.assertEqual(res_csv['Content-Type'], 'text/csv')
        self.assertIn('attachment', res_csv['Content-Disposition'])

        # Test JWT protection
        self.client.logout()
        unauth_response = self.client.get(url_json)
        self.assertEqual(unauth_response.status_code, status.HTTP_401_UNAUTHORIZED)
