from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Budget, Category, Expense, Income

User = get_user_model()

class ExpenseApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='secret123')
        self.client.force_authenticate(user=self.user)
        self.food, _ = Category.objects.get_or_create(name='FOOD', defaults={'icon': 'utensils'})
        self.travel, _ = Category.objects.get_or_create(name='TRAVEL', defaults={'icon': 'plane'})
        Expense.objects.create(user=self.user, title='Lunch', amount=12.50, date_spent='2026-07-10', category=self.food)
        Expense.objects.create(user=self.user, title='Train ticket', amount=45.00, date_spent='2026-07-08', category=self.travel)
        Expense.objects.create(user=self.user, title='Coffee', amount=4.75, date_spent='2026-07-12', category=self.food)

    def test_filter_by_category_id(self):
        url = reverse('expense-list') + f'?category={self.food.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertTrue(all(item['category'] == self.food.id for item in response.data))

    def test_filter_by_category_name(self):
        url = reverse('expense-list') + '?category=food'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_sort_latest_oldest_highest_lowest(self):
        url = reverse('expense-list') + '?sort=latest'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['title'], 'Coffee')

        url = reverse('expense-list') + '?sort=oldest'
        response = self.client.get(url)
        self.assertEqual(response.data[0]['title'], 'Train ticket')

        url = reverse('expense-list') + '?sort=highest'
        response = self.client.get(url)
        self.assertEqual(response.data[0]['title'], 'Train ticket')

        url = reverse('expense-list') + '?sort=lowest'
        response = self.client.get(url)
        self.assertEqual(response.data[0]['title'], 'Coffee')

    def test_total_endpoint(self):
        url = reverse('expense-total')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 62.25)

    def test_total_endpoint_with_filter(self):
        url = reverse('expense-total') + f'?category={self.food.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 17.25)


class SummaryApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='secret123')
        self.client.force_authenticate(user=self.user)
        food, _ = Category.objects.get_or_create(name='FOOD', defaults={'icon': 'utensils'})
        Income.objects.create(user=self.user, title='Salary', source='SALARY', amount=2000, income_date='2026-07-01', description='Monthly salary')
        Expense.objects.create(user=self.user, title='Lunch', amount=15.0, date_spent='2026-07-10', category=food)

    def test_summary_endpoint(self):
        url = reverse('summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_income'], 2000)
        self.assertEqual(response.data['total_expense'], 15)
        self.assertEqual(response.data['current_balance'], 1985)


class BudgetApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='secret123')
        self.client.force_authenticate(user=self.user)
        self.food, _ = Category.objects.get_or_create(name='FOOD', defaults={'icon': 'utensils'})
        self.travel, _ = Category.objects.get_or_create(name='TRAVEL', defaults={'icon': 'plane'})

    def test_create_budget_and_prevent_duplicate_budget(self):
        url = reverse('budget-list')
        payload = {'category': self.food.id, 'budget_amount': '100.00', 'month': 7, 'year': 2026}

        first_response = self.client.post(url, payload, format='json')
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(first_response.data['budget_amount'], '100.00')

        duplicate_response = self.client.post(url, payload, format='json')
        self.assertEqual(duplicate_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', duplicate_response.data)

    def test_budget_summary_endpoint_returns_remaining_and_overspent(self):
        Budget.objects.create(user=self.user, category=self.food, budget_amount=100, month=7, year=2026)
        Expense.objects.create(user=self.user, title='Groceries', amount=140, date_spent='2026-07-12', category=self.food)

        response = self.client.get(reverse('budget-summary'), {'category': self.food.id, 'month': 7, 'year': 2026})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['budget_amount'], '100.00')
        self.assertEqual(response.data['total_expense'], '140.00')
        self.assertEqual(response.data['remaining_budget'], '-40.00')
        self.assertEqual(response.data['overspent_amount'], '40.00')

    def test_dashboard_endpoint_returns_budget_summary_and_recent_transactions(self):
        Income.objects.create(user=self.user, title='Salary', source='SALARY', amount=25000, income_date='2026-07-01', description='Salary')
        Expense.objects.create(user=self.user, title='Rent', amount=18000, date_spent='2026-07-05', category=self.travel)
        Budget.objects.create(user=self.user, category=self.food, budget_amount=22000, month=7, year=2026)

        response = self.client.get(reverse('dashboard'), {'month': 7, 'year': 2026})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data['total_income']), Decimal('25000.00'))
        self.assertEqual(Decimal(response.data['total_expense']), Decimal('18000.00'))
        self.assertEqual(Decimal(response.data['current_balance']), Decimal('7000.00'))
        self.assertEqual(Decimal(response.data['total_budget']), Decimal('22000.00'))
        self.assertEqual(Decimal(response.data['remaining_budget']), Decimal('4000.00'))
        self.assertIn('recent_transactions', response.data)
        self.assertIn('expenses_by_category', response.data)
        self.assertEqual(response.data['expenses_by_category'][0]['category__name'], 'TRAVEL')
        self.assertEqual(Decimal(response.data['expenses_by_category'][0]['total']), Decimal('18000.00'))


class BudgetAlertTasksTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alertuser', password='secret123')
        self.client.force_authenticate(user=self.user)
        self.food, _ = Category.objects.get_or_create(name='Food', defaults={'icon': 'utensils'})
        self.budget = Budget.objects.create(
            user=self.user,
            category=self.food,
            budget_amount=Decimal('100.00'),
            month=8,
            year=2026
        )

    def test_task_1_2_3_4_budget_utilization_and_warning_alerts(self):
        from notifications.models import Notification

        # 1. Below 80%: no warning alert created
        Expense.objects.create(user=self.user, title='Groceries 1', amount=50, date_spent='2026-08-01', category=self.food)
        self.assertFalse(Notification.objects.filter(user=self.user, title='Warning Alert').exists())

        # 2. Hit 80%: Warning Alert generated
        Expense.objects.create(user=self.user, title='Groceries 2', amount=30, date_spent='2026-08-02', category=self.food)
        warn_notif = Notification.objects.filter(user=self.user, title='Warning Alert').first()
        self.assertIsNotNone(warn_notif)
        self.assertIn('80%', warn_notif.message)
        self.assertIn('Food', warn_notif.message)

        # 3. Duplicate prevention: adding another small expense keeping utilization between 80% and 89% does not duplicate 80% alert
        Expense.objects.create(user=self.user, title='Coffee', amount=5, date_spent='2026-08-03', category=self.food)
        self.assertEqual(Notification.objects.filter(user=self.user, title='Warning Alert').count(), 1)

        # 4. Hit 90%: High Warning Alert generated
        Expense.objects.create(user=self.user, title='Dinner', amount=7, date_spent='2026-08-04', category=self.food)
        high_notif = Notification.objects.filter(user=self.user, title='High Warning Alert').first()
        self.assertIsNotNone(high_notif)
        self.assertIn('92%', high_notif.message)

        # 5. Hit 100%+: Budget Exceeded Alert generated
        Expense.objects.create(user=self.user, title='Snacks', amount=10, date_spent='2026-08-05', category=self.food)
        exceeded_notif = Notification.objects.filter(user=self.user, title='Budget Exceeded Alert').first()
        self.assertIsNotNone(exceeded_notif)
        self.assertEqual(exceeded_notif.notification_type, 'ERROR')
        self.assertEqual(exceeded_notif.priority, 3)

    def test_task_5_budget_alert_api_jwt_protected(self):
        from notifications.models import Notification

        Expense.objects.create(user=self.user, title='Groceries', amount=90, date_spent='2026-08-01', category=self.food)

        # Test authenticated call
        url = reverse('budgetalert-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)
        item = response.data[0]

        # Check required fields in API
        self.assertEqual(item['budget_category'], 'Food')
        self.assertEqual(item['Budget Category'], 'Food')
        self.assertEqual(item['budget_amount'], '100.00')
        self.assertEqual(item['total_expense'], '90.00')
        self.assertEqual(item['budget_utilization_percentage'], 90.0)
        self.assertEqual(item['alert_level'], 'High Warning Alert')
        self.assertIn('90%', item['alert_message'])

        # Test unauthenticated call -> 401 Unauthorized
        self.client.logout()
        unauth_response = self.client.get(url)
        self.assertEqual(unauth_response.status_code, status.HTTP_401_UNAUTHORIZED)

