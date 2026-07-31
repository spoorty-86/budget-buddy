from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

class AccountRegistrationTests(APITestCase):
    def test_register_creates_user(self):
        url = reverse('register')
        data = {
            'username': 'newuser123',
            'email': 'newuser123@example.com',
            'password': 'secret123',
            'full_name': 'New User',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser123').exists())
        self.assertEqual(response.data['username'], 'newuser123')

    def test_register_sends_welcome_email(self):
        from django.core import mail
        url = reverse('register')
        data = {
            'username': 'emailuser',
            'email': 'emailuser@example.com',
            'password': 'secure123',
            'full_name': 'Email User',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Welcome to BudgetBuddy', mail.outbox[0].subject)
        self.assertIn('Your account has been created successfully', mail.outbox[0].body)

    def test_register_duplicate_username_returns_error(self):
        User.objects.create_user(username='existing', password='secret123', email='existing@example.com')
        url = reverse('register')
        response = self.client.post(url, {
            'username': 'existing',
            'email': 'other@example.com',
            'password': 'secret123',
            'full_name': 'Existing User',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)


class PasswordResetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='resetuser',
            password='initialpass',
            email='resetuser@example.com'
        )

    def test_password_reset_with_matching_username_and_email(self):
        url = reverse('password_reset')
        response = self.client.post(url, {
            'username': 'resetuser',
            'email': 'resetuser@example.com',
            'new_password': 'newstrongpass',
            'confirm_password': 'newstrongpass',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('detail', response.data)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newstrongpass'))

    def test_password_reset_with_incorrect_email_returns_error(self):
        url = reverse('password_reset')
        response = self.client.post(url, {
            'username': 'resetuser',
            'email': 'wrong@example.com',
            'new_password': 'newstrongpass',
            'confirm_password': 'newstrongpass',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_password_reset_passwords_must_match(self):
        url = reverse('password_reset')
        response = self.client.post(url, {
            'username': 'resetuser',
            'email': 'resetuser@example.com',
            'new_password': 'newstrongpass',
            'confirm_password': 'differentpass',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('confirm_password', response.data)
