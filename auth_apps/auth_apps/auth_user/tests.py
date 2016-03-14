from django.core.urlresolvers import reverse_lazy
from django.test import override_settings
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

    @override_settings(
        SECURE_SSL_REDIRECT=False
    )
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

    @override_settings(
        SECURE_SSL_REDIRECT=False
    )
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
        user_url = reverse_lazy('v1:api_user_resource', kwargs={'pk': 1})
        response = self.client.get(user_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data.get('username'), self.test_user.username)

    @override_settings(
        SECURE_SSL_REDIRECT=False
    )
    def test_reset_with_incorrect_code(self):
        # reset user password
        new_password = '123456'
        data = {
            'new_password': new_password,
            'code': '123456',  # wrong code
        }
        response = self.client.post(self.reset_url, data, format='json')
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)
