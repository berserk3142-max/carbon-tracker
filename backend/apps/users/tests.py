from django.test import TestCase
from rest_framework.test import APIClient

from apps.organizations.models import Organization
from apps.users.models import User


class AuthAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_login_and_me_work(self):
        response = self.client.post('/api/auth/register/', {
            'username': 'newadmin',
            'email': 'newadmin@example.com',
            'password': 'secret123',
            'first_name': 'New',
            'last_name': 'Admin',
            'organization_name': 'NewCo',
            'industry': 'technology',
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertIn('access', response.data['tokens'])
        self.assertEqual(Organization.objects.get(name='NewCo').industry, 'technology')
        self.assertEqual(User.objects.get(username='newadmin').role, 'admin')

        login_response = self.client.post('/api/auth/login/', {
            'username': 'newadmin',
            'password': 'secret123',
        }, format='json')

        self.assertEqual(login_response.status_code, 200)
        token = login_response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        me_response = self.client.get('/api/auth/me/')
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.data['username'], 'newadmin')
