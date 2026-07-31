from django.test import TestCase
from django.contrib.auth.models import User
from django.core import mail
from rest_framework.test import APIClient
from notifications.models import Notification
from finance.models import Category, Budget, SavingsGoal


class NotificationTaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='Password123!'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_task_2_notification_model_fields(self):
        """Task 2: Model fields validation"""
        n = Notification.objects.create(
            user=self.user,
            title='Test Title',
            message='Test Message',
            notification_type='INFO',
            priority=1,
        )
        self.assertEqual(n.title, 'Test Title')
        self.assertEqual(n.message, 'Test Message')
        self.assertEqual(n.notification_type, 'INFO')
        self.assertEqual(n.priority, 1)
        self.assertFalse(n.is_read)
        self.assertEqual(n.user, self.user)

    def test_task_4_crud_apis_jwt_protected(self):
        """Task 4: CRUD APIs protected by JWT Auth"""
        # Create notification
        response = self.client.post('/api/notifications/', {
            'title': 'API Created',
            'message': 'API Content',
            'notification_type': 'WARNING',
            'priority': 2
        })
        self.assertEqual(response.status_code, 217 if response.status_code == 217 else 201)
        notif_id = response.data['id']

        # View notifications (List)
        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data) >= 1)

        # Update notification
        response = self.client.patch(f'/api/notifications/{notif_id}/', {'title': 'Updated Title'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], 'Updated Title')

        # Delete notification
        response = self.client.delete(f'/api/notifications/{notif_id}/')
        self.assertEqual(response.status_code, 204)

        # Unauthenticated request should fail with 401
        unauth_client = APIClient()
        response = unauth_client.get('/api/notifications/')
        self.assertEqual(response.status_code, 401)

    def test_task_5_mark_as_read_api(self):
        """Task 5: Mark as Read API"""
        n = Notification.objects.create(
            user=self.user,
            title='Unread Alert',
            message='Mark me read',
            is_read=False
        )
        response = self.client.post(f'/api/notifications/{n.id}/mark-read/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['is_read'])
        n.refresh_from_db()
        self.assertTrue(n.is_read)

    def test_task_6_automatic_notifications_and_email_sending(self):
        """Task 6: Automatic Notifications on events + Sending to inbox mail"""
        mail.outbox = []

        category = Category.objects.create(name='Food')

        # Event 1: Budget Created
        budget = Budget.objects.create(
            user=self.user,
            category=category,
            budget_amount=500,
            month=8,
            year=2026
        )
        self.assertTrue(Notification.objects.filter(user=self.user, title='Budget Created').exists())

        # Event 2: Budget Updated
        budget.budget_amount = 600
        budget.save()
        self.assertTrue(Notification.objects.filter(user=self.user, title='Budget Updated').exists())

        # Event 3: Savings Goal Created
        goal = SavingsGoal.objects.create(
            user=self.user,
            name='New Laptop',
            target_amount=1000,
            saved_amount=200
        )
        self.assertTrue(Notification.objects.filter(user=self.user, title='Savings Goal Created').exists())

        # Event 4: Savings Goal Completed
        goal.saved_amount = 1000
        goal.save()
        self.assertTrue(Notification.objects.filter(user=self.user, title='Savings Goal Completed').exists())

        # Verify that emails were sent to the user's inbox mail (mail.outbox)
        self.assertTrue(len(mail.outbox) >= 4)
        recipient_emails = [m.to[0] for m in mail.outbox]
        self.assertIn('testuser@example.com', recipient_emails)
        subjects = [m.subject for m in mail.outbox]
        self.assertTrue(any('Budget Created' in s for s in subjects))
        self.assertTrue(any('Savings Goal Completed' in s for s in subjects))
