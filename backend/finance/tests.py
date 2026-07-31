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
