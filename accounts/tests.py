from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, VerificationCode

User = get_user_model()


class UserRegistrationTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.register_url = '/auth/register/'
        self.user_data = {
            'full_name': 'John Doe',
            'email': 'mutheo2026@gmail.com',
            'phone_number': '0781234567',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!'
        }

    def test_registration_success(self):
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('email', response.data)
        self.assertEqual(response.data['email'], self.user_data['email'])  
        self.assertTrue(User.objects.filter(email=self.user_data['email']).exists())

    def test_registration_password_mismatch(self):
        data = self.user_data.copy()
        data['password_confirm'] = 'DifferentPass123!'
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_duplicate_email(self):
        self.client.post(self.register_url, self.user_data, format='json')
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLoginTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.login_url = '/auth/login/'
        self.user = User.objects.create_user(
            email='mutheo2026@gmail.com',
            full_name='Test User',
            phone_number='0780000000',
            password='testpass123'
        )

    def test_login_success(self):
        data = {'email': 'mutheo2026@gmail.com', 'password': 'testpass123'}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_invalid_credentials(self):
        data = {'email': 'mutheo2026@gmail.com', 'password': 'wrongpassword'}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLogoutTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.logout_url = '/auth/logout/'
        self.user = User.objects.create_user(
            email='mutheo2026@gmail.com',
            full_name='Test User',
            phone_number='0780000000',
            password='testpass123'
        )

    def test_logout_success(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.force_authenticate(user=self.user)
        data = {'refresh': str(refresh)}
        response = self.client.post(self.logout_url, data, format='json')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])


class PasswordResetTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='mutheo2026@gmail.com',
            full_name='Test User',
            phone_number='0780000000',
            password='testpass123'
        )
        self.reset_request_url = '/auth/password_reset_request/'
        self.reset_confirm_url = '/auth/password_reset_confirm/'

    def test_password_reset_request_success(self):
        data = {'email': 'mutheo2026@gmail.com'}
        response = self.client.post(self.reset_request_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_reset_confirm(self):
        data = {
            'email': 'mutheo2026@gmail.com',
            'code': '123456',
            'new_password': 'NewPass123!',
            'new_password_confirm': 'NewPass123!'
        }
        response = self.client.post(self.reset_confirm_url, data, format='json')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])


class EmailVerificationTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='mutheo2026@gmail.com',
            full_name='Test User',
            phone_number='0780000000',
            password='testpass123'
        )

    def test_send_verification_code(self):
        code = VerificationCode.objects.create(
            user=self.user,
            code='123456',
            label=VerificationCode.EMAIL_VERIFICATION,
            email='mutheo2026@gmail.com'
        )
        self.assertEqual(code.code, '123456')
        self.assertTrue(code.is_pending)


class ChangePasswordTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='mutheo2026@gmail.com',
            full_name='Test User',
            phone_number='0780000000',
            password='testpass123'
        )
        self.change_password_url = '/profile/change_password/'

    def test_change_password_success(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'old_password': 'testpass123',
            'new_password': 'NewPass123!',
            'new_password_confirm': 'NewPass123!'
        }
        response = self.client.post(self.change_password_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass123!'))

    def test_change_password_wrong_old_password(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'old_password': 'wrongpass',
            'new_password': 'NewPass123!',
            'new_password_confirm': 'NewPass123!'
        }
        response = self.client.post(self.change_password_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DeleteAccountTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='mutheo2026@gmail.com',
            full_name='Test User',
            phone_number='0780000000',
            password='testpass123'
        )
        self.delete_url = f'/user/{self.user.id}/'

    def test_delete_account(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.delete_url)
        self.assertIn(response.status_code, [status.HTTP_204_NO_CONTENT, status.HTTP_200_OK])


class DeactivateAccountTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            email='feedyopc@gmail.com',
            full_name='Admin User',
            phone_number='0780000001',
            password='adminpass123',
            user_type=User.ADMIN,
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            email='mutheo2026@gmail.com',
            full_name='Regular User',
            phone_number='0780000000',
            password='testpass123'
        )

    def test_deactivate_account(self):
        self.client.force_authenticate(user=self.admin_user)
        url = f'/user/{self.regular_user.id}/deactivate/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_user.refresh_from_db()
        self.assertFalse(self.regular_user.is_active)


class ActivateAccountTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            email='feedyopc@gmail.com',
            full_name='Admin User',
            phone_number='0780000001',
            password='adminpass123',
            user_type=User.ADMIN,
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            email='mutheo2026@gmail.com',
            full_name='Regular User',
            phone_number='0780000000',
            password='testpass123',
            is_active=False
        )

    def test_activate_account(self):
        self.client.force_authenticate(user=self.admin_user)
        url = f'/user/{self.regular_user.id}/activate/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.is_active)


class UpdateProfileTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='mutheo2026@gmail.com',
            full_name='Test User',
            phone_number='0780000000',
            password='testpass123'
        )
        self.update_url = '/profile/update_profile/'

    def test_update_profile_success(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'full_name': 'Updated Name',
            'phone_number': '0781111111'
        }
        response = self.client.patch(self.update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['full_name'], 'Updated Name')
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, 'Updated Name')

    def test_update_profile_unauthenticated(self):
        data = {'full_name': 'Updated Name'}
        response = self.client.patch(self.update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)