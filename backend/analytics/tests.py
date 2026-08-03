import uuid
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from finance.models import Income, Expense, Budget, SavingsGoal, Category

User = get_user_model()


class FinancialSummaryApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username=f'user_{uuid.uuid4().hex[:8]}', password='password123')
        self.client.force_authenticate(user=self.user)
        self.food = Category.objects.create(name=f'Cat_{uuid.uuid4().hex[:8]}', icon='utensils')

        # Setup test financial records:
        # Total Income = 5000.00
        Income.objects.create(user=self.user, title='Salary', source='SALARY', amount=Decimal('5000.00'), income_date='2026-08-01')

        # Total Savings = 1200.00
        SavingsGoal.objects.create(user=self.user, name='Emergency Fund', target_amount=Decimal('5000.00'), saved_amount=Decimal('1200.00'))

        # Create Budget first (Total Budget = 2000.00)
        Budget.objects.create(user=self.user, category=self.food, budget_amount=Decimal('2000.00'), monthly_limit=Decimal('2000.00'), month=8, year=2026)

        # Create Expenses (Total Expense = 1500.00)
        Expense.objects.create(user=self.user, title='Groceries', amount=Decimal('500.00'), date_spent='2026-08-02', category=self.food)
        Expense.objects.create(user=self.user, title='Rent', amount=Decimal('1000.00'), date_spent='2026-08-03', category=self.food)

    def test_financial_summary_endpoint(self):
        url = reverse('analytics-summary')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        # Verify exact calculations:
        # Current Balance = Total Income (5000) - Total Expense (1500) = 3500.00
        self.assertEqual(Decimal(str(data['total_income'])), Decimal('5000.00'))
        self.assertEqual(Decimal(str(data['total_expense'])), Decimal('1500.00'))
        self.assertEqual(Decimal(str(data['current_balance'])), Decimal('3500.00'))
        self.assertEqual(Decimal(str(data['total_savings'])), Decimal('1200.00'))
        self.assertEqual(Decimal(str(data['remaining_budget'])), Decimal('500.00'))

        # Also verify Title Case keys:
        self.assertEqual(Decimal(str(data['Total Income'])), Decimal('5000.00'))
        self.assertEqual(Decimal(str(data['Total Expense'])), Decimal('1500.00'))
        self.assertEqual(Decimal(str(data['Current Balance'])), Decimal('3500.00'))

    def test_financial_summary_unauthenticated(self):
        self.client.logout()
        url = reverse('analytics-summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CategoryExpenseAnalysisTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username=f'cat_user_{uuid.uuid4().hex[:8]}', password='password123')
        self.client.force_authenticate(user=self.user)
        self.food = Category.objects.create(name=f'Food_{uuid.uuid4().hex[:4]}', icon='utensils')
        self.shopping = Category.objects.create(name=f'Shopping_{uuid.uuid4().hex[:4]}', icon='shopping-bag')

        # Food total = 4500.00
        Expense.objects.create(user=self.user, title='Groceries', amount=Decimal('4500.00'), date_spent='2026-08-01', category=self.food)
        # Shopping total = 7200.00
        Expense.objects.create(user=self.user, title='Clothes', amount=Decimal('7200.00'), date_spent='2026-08-02', category=self.shopping)

    def test_category_expense_analysis(self):
        url = reverse('analytics-category-expenses')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        # Dict representation
        self.assertEqual(Decimal(str(data[self.food.name])), Decimal('4500.00'))
        self.assertEqual(Decimal(str(data[self.shopping.name])), Decimal('7200.00'))

    def test_category_expense_analysis_format_list(self):
        url = reverse('analytics-category-expenses') + '?type=list'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 2)


class MonthlyExpenseTrendTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username=f'month_user_{uuid.uuid4().hex[:8]}', password='password123')
        self.client.force_authenticate(user=self.user)

        # January -> 8500
        Expense.objects.create(user=self.user, title='Jan Exp', amount=Decimal('8500.00'), date_spent='2026-01-15')
        # February -> 7600
        Expense.objects.create(user=self.user, title='Feb Exp', amount=Decimal('7600.00'), date_spent='2026-02-10')
        # March -> 9100
        Expense.objects.create(user=self.user, title='Mar Exp', amount=Decimal('9100.00'), date_spent='2026-03-20')
        # April -> 6900
        Expense.objects.create(user=self.user, title='Apr Exp', amount=Decimal('6900.00'), date_spent='2026-04-05')

    def test_monthly_expense_trend(self):
        url = reverse('analytics-monthly-expenses')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertEqual(Decimal(str(data['January'])), Decimal('8500.00'))
        self.assertEqual(Decimal(str(data['February'])), Decimal('7600.00'))
        self.assertEqual(Decimal(str(data['March'])), Decimal('9100.00'))
        self.assertEqual(Decimal(str(data['April'])), Decimal('6900.00'))

    def test_monthly_expense_trend_format_list(self):
        url = reverse('analytics-monthly-expenses') + '?type=list'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 4)


class ExpenseExtremesTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username=f'ext_user_{uuid.uuid4().hex[:8]}', password='password123')
        self.client.force_authenticate(user=self.user)

        Expense.objects.create(user=self.user, title='Cheap Snack', amount=Decimal('5.00'), date_spent='2026-01-01')
        Expense.objects.create(user=self.user, title='Expensive Laptop', amount=Decimal('2500.00'), date_spent='2026-02-15')
        Expense.objects.create(user=self.user, title='Recent Expense', amount=Decimal('100.00'), date_spent='2026-08-01')

    def test_expense_extremes_endpoint(self):
        url = reverse('analytics-highest-lowest-expenses')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertEqual(Decimal(data['highest_expense']['amount']), Decimal('2500.00'))
        self.assertEqual(Decimal(data['lowest_expense']['amount']), Decimal('5.00'))
        self.assertEqual(data['latest_expense']['title'], 'Recent Expense')
        self.assertEqual(data['oldest_expense']['title'], 'Cheap Snack')


class UnifiedDashboardApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username=f'dash_user_{uuid.uuid4().hex[:8]}', password='password123')
        self.client.force_authenticate(user=self.user)
        self.food = Category.objects.create(name=f'Food_{uuid.uuid4().hex[:4]}', icon='utensils')

        Income.objects.create(user=self.user, title='Salary', source='SALARY', amount=Decimal('4000.00'), income_date='2026-08-01')
        Expense.objects.create(user=self.user, title='Groceries', amount=Decimal('1200.00'), date_spent='2026-08-02', category=self.food)
        SavingsGoal.objects.create(user=self.user, name='Car Fund', target_amount=Decimal('10000.00'), saved_amount=Decimal('3000.00'))

    def test_unified_dashboard_api(self):
        url = reverse('analytics-dashboard')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        # Verify Task 6 combined response sections
        self.assertIn('financial_summary', data)
        self.assertIn('category_wise_analysis', data)
        self.assertIn('monthly_trend', data)
        self.assertIn('recent_transactions', data)
        self.assertIn('latest_notifications', data)
        self.assertIn('active_savings_goals', data)

        # Check section values
        self.assertEqual(Decimal(str(data['financial_summary']['total_income'])), Decimal('4000.00'))
        self.assertEqual(Decimal(str(data['financial_summary']['total_expense'])), Decimal('1200.00'))
        self.assertEqual(Decimal(str(data['financial_summary']['current_balance'])), Decimal('2800.00'))
        self.assertEqual(len(data['active_savings_goals']), 1)


