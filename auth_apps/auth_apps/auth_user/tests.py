from django.core.urlresolvers import reverse_lazy
# from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from oauth2_provider.models import get_application_model, AccessToken
from django.core.cache import cache

from .models import TechUUser


class OAuth2APITestCase(APITestCase):
    def init_application(self, user):
        self._application_model = get_application_model()
        self._application = self._application_model(
            name='test application',
            redirect_uris='https://localhost',
            user=user,
            client_type=self._application_model.CLIENT_CONFIDENTIAL,
            authorization_grant_type=self._application_model.GRANT_PASSWORD,
        )
        self._application.save()

    def generate_token(self, user, access_token, scope):
        from datetime import timedelta
        from django.utils import timezone
        token_obj = AccessToken.objects.create(
            user=user,
            token=access_token,
            application=self._application,
            scope=scope,
            expires=timezone.now() + timedelta(days=1)
        )
        return token_obj


class RegisterMobileUserTestCase(APITestCase):
    def setUp(self):
        cache.clear()
        self.register_url = reverse_lazy('v1:api_user_register_mobile')
        self.register_code_url = reverse_lazy('v1:api_register_mobile_code')

    def tearDown(self):
        cache.clear()

    def test_minimal_register(self):
        mobile = '15911186897'
        # get mobile code
        data = {
            'mobile': mobile,
        }
        response = self.client.post(
            self.register_code_url, data, format='json')
        mobile_code = response.data.get('code')
        self.assertTrue(mobile_code)
        self.assertEqual(len(mobile_code), 6)
        # register user
        data = {
            'mobile': mobile,
            'password': '123456',
            'code': mobile_code
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TechUUser.objects.count(), 1)
        self.assertEqual(TechUUser.objects.get().mobile, mobile)
        self.assertTrue(TechUUser.objects.get().username)


class RegisterBackendUserTestCase(APITestCase):
    def setUp(self):
        cache.clear()
        self.register_url = reverse_lazy('v1:api_user_register_backend')

    def tearDown(self):
        cache.clear()

    def test_minimal_register(self):
        username = 'accountcenter'
        data = {
            'username': username,
            'email': 'accountcenter@163.com',
            'password': '123456'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TechUUser.objects.count(), 1)
        self.assertEqual(TechUUser.objects.get().username, username)


class MobileCodeResetPasswordTestCase(OAuth2APITestCase):
    def setUp(self):
        cache.clear()
        self.code_url = reverse_lazy('v1:api_mobile_code')
        self.reset_url = reverse_lazy('v1:api_user_reset_password_mobile')
        test_user = {
            'username': 'test',
            'mobile': '15911186897',
            'password': 'test',
        }
        user = TechUUser.objects.create_user(**test_user)
        self.test_user = user
        self.init_application(user)

    def tearDown(self):
        cache.clear()

    def test_reset_success(self):
        self.assertEqual(TechUUser.objects.count(), 1)
        self.assertTrue(TechUUser.objects.get().is_active)
        self.assertTrue(TechUUser.objects.get().has_usable_password())
        self.assertEqual(TechUUser.objects.get().mobile, self.test_user.mobile)
        # get mobile code
        data = {
            'mobile': self.test_user.mobile,
        }
        response = self.client.post(
            self.code_url, data, format='json')
        mobile_code = response.data.get('code')
        self.assertTrue(mobile_code)
        self.assertEqual(len(mobile_code), 6)
        # reset user password
        new_password = '123456'
        data = {
            'mobile': self.test_user.mobile,
            'new_password': new_password,
            'code': mobile_code,
        }
        response = self.client.post(self.reset_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # generate access token
        access_token = '1234567890'
        scope = 'user'
        token = self.generate_token(self.test_user, access_token, scope)
        self.assertTrue(token.is_valid())
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token.token)
        # get user info
        user_url = reverse_lazy(
            'v1:api_user_resource', kwargs={'pk': self.test_user.pk})
        response = self.client.get(user_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data.get('username'), self.test_user.username)

    def test_reset_with_incorrect_code(self):
        self.assertEqual(TechUUser.objects.count(), 1)
        # reset user password
        new_password = '123456'
        data = {
            'new_password': new_password,
            'code': '123456',  # wrong code
        }
        response = self.client.post(self.reset_url, data, format='json')
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)


class ChangePasswordTestCase(OAuth2APITestCase):
    def setUp(self):
        cache.clear()
        self.change_url = reverse_lazy('v1:api_user_change_password')
        test_user = {
            'username': 'test',
            'mobile': '15911186897',
            'password': 'test',
        }
        user = TechUUser.objects.create_user(**test_user)
        self.test_user = user
        self.init_application(user)

    def tearDown(self):
        cache.clear()

    def test_change_success(self):
        self.assertEqual(TechUUser.objects.count(), 1)
        # generate access token
        access_token = '1234567890'
        scope = 'user'
        token = self.generate_token(self.test_user, access_token, scope)
        self.assertTrue(token.is_valid())
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token.token)
        # change password
        data = {
            'old_password': 'test',
            'new_password': 'test1',
        }
        response = self.client.post(self.change_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # fresh user
        test_user = TechUUser.objects.get()
        self.assertTrue(test_user.check_password(data.get('new_password')))
        self.assertFalse(test_user.check_password(data.get('old_password')))

    def test_change_password_without_token(self):
        self.assertEqual(TechUUser.objects.count(), 1)
        # change password without token
        data = {
            'old_password': 'test',
            'new_password': 'test1',
        }
        response = self.client.post(self.change_url, data, format='json')
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # fresh user
        test_user = TechUUser.objects.get()
        self.assertFalse(test_user.check_password(data.get('new_password')))
        self.assertTrue(test_user.check_password(data.get('old_password')))

    def test_change_password_with_wrong_old_password(self):
        self.assertEqual(TechUUser.objects.count(), 1)
        # generate access token
        access_token = '1234567890'
        scope = 'user'
        token = self.generate_token(self.test_user, access_token, scope)
        self.assertTrue(token.is_valid())
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token.token)
        # change password
        data = {
            'old_password': 'wrong_password',
            'new_password': 'test1',
        }
        response = self.client.post(self.change_url, data, format='json')
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        # fresh user
        test_user = TechUUser.objects.get()
        self.assertFalse(test_user.check_password(data.get('new_password')))
        self.assertFalse(test_user.check_password(data.get('old_password')))
        self.assertTrue(test_user.check_password('test'))
