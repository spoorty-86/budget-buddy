from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from finance.models import Category, Expense, Income, Budget, SavingsGoal
import datetime

from decimal import Decimal

User = get_user_model()

class AiPortalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='aitestuser', password='password123', email='ai@test.com')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.category = Category.objects.create(name='Groceries')
        Income.objects.create(user=self.user, title='Salary', amount=Decimal('3000.00'), income_date=datetime.date.today())
        Expense.objects.create(user=self.user, title='Target Groceries', amount=Decimal('150.00'), category=self.category, date_spent=datetime.date.today())
        Budget.objects.create(user=self.user, category=self.category, monthly_limit=Decimal('500.00'), budget_amount=Decimal('500.00'), month=datetime.date.today().month, year=datetime.date.today().year)
        SavingsGoal.objects.create(user=self.user, name='Emergency Fund', target_amount=Decimal('1000.00'), saved_amount=Decimal('250.00'))

    def test_ai_insights_endpoint(self):
        response = self.client.get('/api/ai/insights/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('health_score', response.data)
        self.assertIn('insights', response.data)
        self.assertIn('forecast', response.data)
        self.assertGreater(response.data['health_score'], 0)

    def test_ai_chat_endpoint(self):
        response = self.client.post('/api/ai/chat/', {'prompt': 'Where is my highest spending?'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('reply', response.data)
        self.assertIn('Groceries', response.data['reply'])

    def test_ai_chat_saved_amount_specific_question(self):
        response = self.client.post('/api/ai/chat/', {'prompt': 'how much amount i saved'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('reply', response.data)
        self.assertIn('2850.00', response.data['reply'])
        self.assertIn('saved', response.data['reply'].lower())

    def test_ai_chat_conversational_greeting(self):
        response = self.client.post('/api/ai/chat/', {'prompt': 'how are you'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('reply', response.data)
        self.assertIn("great", response.data['reply'].lower())

    def test_ai_parse_expense(self):
        response = self.client.post('/api/ai/parse-expense/', {'text': 'Spent $65.50 on groceries yesterday', 'auto_save': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['amount'], 65.50)
        self.assertIn('created_expense', response.data)

    def test_ai_simulate(self):
        response = self.client.post('/api/ai/simulate/', {'income_change': 500, 'expense_cut_pct': 10}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('simulated', response.data)
        self.assertGreater(response.data['simulated']['net_savings'], response.data['baseline']['net_savings'])
