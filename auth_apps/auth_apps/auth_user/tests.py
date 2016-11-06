# coding: utf-8
from __future__ import unicode_literals

import mock
from django.core.urlresolvers import reverse_lazy, reverse
from django.core.cache import cache
from django.conf import settings
from django.test import LiveServerTestCase
# from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from oauth2_provider.models import get_application_model, AccessToken

from .models import TechUUser


class MockCreateUserMixin(object):
    def create_user(self, **data):
        with mock.patch('auth_user.signals.xplatform_register') as mock_task:
            user = TechUUser.objects.create(**data)
            mock_task.delay.assert_called_once_with([{
                'username': user.username,
                'password': data.get('password'),
                'nickname': user.nickname or user.username,
            }])
            return user
        return None


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

    @mock.patch('auth_user.views.send_mobile_task')
    @mock.patch('auth_user.signals.xplatform_register')
    def test_minimal_register(self, mock_task, mock_mobile_task):
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
        self.assertTrue(mock_mobile_task.delay.called)
        self.assertEqual(mock_mobile_task.delay.call_count, 1)
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

        user = TechUUser.objects.get()
        register_entries = [{
            'username': user.username,
            'password': data.get('password'),
            'nickname': user.nickname or user.username,
        }]
        mock_task.delay.assert_called_once_with(
            register_entries)


class RegisterBackendUserTestCase(APITestCase):
    def setUp(self):
        cache.clear()
        self.register_url = reverse_lazy('v1:api_user_register_backend')

    def tearDown(self):
        cache.clear()

    @mock.patch('auth_user.signals.xplatform_register')
    def test_minimal_register(self, mock_task):
        username = 'accountcenter'
        data = {
            'username': username,
            'nickname': username,
            'password': '123456'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TechUUser.objects.count(), 1)
        self.assertEqual(TechUUser.objects.get().username, username)

        mock_task.delay.assert_called_once_with(
            [data])


class ResetPasswordBackendTestCase(MockCreateUserMixin, APITestCase):
    def setUp(self):
        cache.clear()
        self.reset_url = reverse_lazy('v1:api_user_reset_password_backend')
        test_user = {
            'username': 'test',
            'mobile': '15911186897',
            'password': 'test',
        }
        self.test_user = test_user
        self.create_user(**test_user)

    def tearDown(self):
        cache.clear()

    def test_invalid_identity(self):
        identity = 'invalid_id'
        data = {
            'identity': identity,
            'hashed_password': '123456'
        }
        response = self.client.post(self.reset_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # query DB to check
        self.assertEqual(TechUUser.objects.count(), 1)
        user = TechUUser.objects.get(username=self.test_user.get('username'))
        self.assertTrue(user)
        self.assertTrue(user.check_password('test'))

    def test_reset_success(self):
        import hashlib
        from .hashers import TechUPasswordHasher as hasher
        identity = 'test'
        raw_password = '123456'
        data = {
            'identity': identity,
            'hashed_password': hashlib.md5(
                settings.TECHU_BACKEND_SALT + identity + hashlib.md5(
                    hasher.FRONTEND_SALT + raw_password
                ).hexdigest()
            ).hexdigest()
        }
        response = self.client.post(self.reset_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TechUUser.objects.count(), 1)
        user = TechUUser.objects.get()
        print user.password
        self.assertTrue(user)
        self.assertTrue(user.check_password(raw_password))


class MobileCodeResetPasswordTestCase(MockCreateUserMixin, OAuth2APITestCase):
    def setUp(self):
        cache.clear()
        self.code_url = reverse_lazy('v1:api_mobile_code')
        self.reset_url = reverse_lazy('v1:api_user_reset_password_mobile')
        test_user = {
            'username': 'test',
            'mobile': '15911186897',
            'password': 'test',
        }
        self.test_user = test_user
        user = self.create_user(**test_user)
        self.init_application(user)

    def tearDown(self):
        cache.clear()

    @mock.patch('auth_user.views.send_mobile_task')
    @mock.patch('auth_user.signals.xplatform_changepwd')
    def test_reset_success(self, mock_task, mock_mobile_task):
        self.assertEqual(TechUUser.objects.count(), 1)
        self.assertTrue(TechUUser.objects.get().is_active)
        self.assertTrue(TechUUser.objects.get().has_usable_password())
        self.assertEqual(
            TechUUser.objects.get().mobile, self.test_user.get('mobile')
        )
        user = TechUUser.objects.get()
        self.assertTrue(user)
        # get mobile code
        data = {
            'mobile': user.mobile,
        }
        response = self.client.post(
            self.code_url, data, format='json')
        mobile_code = response.data.get('code')
        self.assertTrue(mobile_code)
        self.assertEqual(len(mobile_code), 6)
        self.assertTrue(mock_mobile_task.delay.called)
        self.assertEqual(mock_mobile_task.delay.call_count, 1)
        # reset user password
        new_password = '123456'
        data = {
            'mobile': user.mobile,
            'new_password': new_password,
            'code': mobile_code,
        }
        response = self.client.post(self.reset_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_task.delay.assert_called_once_with(
            None, user.username, new_password)

        # generate access token
        access_token = '1234567890'
        scope = 'user'
        token = self.generate_token(user, access_token, scope)
        self.assertTrue(token.is_valid())
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token.token)
        # get user info
        user_url = reverse_lazy(
            'v1:api_user_resource', kwargs={'pk': user.pk})
        response = self.client.get(user_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data.get('username'), user.username)

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


class ChangePasswordTestCase(MockCreateUserMixin, OAuth2APITestCase):
    def setUp(self):
        cache.clear()
        self.change_url = reverse_lazy('v1:api_user_change_password')
        test_user = {
            'username': 'test',
            'mobile': '15911186897',
            'password': 'test',
        }
        self.test_user = test_user
        user = self.create_user(**test_user)
        self.init_application(user)

    def tearDown(self):
        cache.clear()

    @mock.patch('auth_user.signals.xplatform_changepwd')
    def test_change_success(self, mock_task):
        self.assertEqual(TechUUser.objects.count(), 1)
        user = TechUUser.objects.get()
        self.assertTrue(user)
        # generate access token
        access_token = '1234567890'
        scope = 'user'
        token = self.generate_token(user, access_token, scope)
        self.assertTrue(token.is_valid())
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token.token)
        # change password
        data = {
            'old_password': 'test',
            'new_password': 'test1',
        }
        response = self.client.post(self.change_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_task.delay.assert_called_once_with(
            None, user.username, data.get('new_password'))

        # fresh user
        fresh_user = TechUUser.objects.get()
        self.assertTrue(fresh_user.check_password(data.get('new_password')))
        self.assertFalse(fresh_user.check_password(data.get('old_password')))

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
        fresh_user = TechUUser.objects.get()
        self.assertFalse(fresh_user.check_password(data.get('new_password')))
        self.assertTrue(fresh_user.check_password(data.get('old_password')))

    def test_change_password_with_wrong_old_password(self):
        self.assertEqual(TechUUser.objects.count(), 1)
        user = TechUUser.objects.get()
        self.assertTrue(user)
        # generate access token
        access_token = '1234567890'
        scope = 'user'
        token = self.generate_token(user, access_token, scope)
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
        fresh_user = TechUUser.objects.get()
        self.assertFalse(fresh_user.check_password(data.get('new_password')))
        self.assertFalse(fresh_user.check_password(data.get('old_password')))
        self.assertTrue(fresh_user.check_password('test'))


class UserRetrieveUpdateTestCase(MockCreateUserMixin, OAuth2APITestCase):
    def setUp(self):
        cache.clear()
        test_user = {
            'username': 'test',
            'mobile': '15911186897',
            'password': 'test',
        }
        self.test_user = test_user
        user = self.create_user(**test_user)
        self.init_application(user)

    def tearDown(self):
        cache.clear()
       
    def test_update_user(self):
        self.assertEqual(TechUUser.objects.count(), 1)
        user = TechUUser.objects.get()
        self.assertTrue(user)
        # generate access token
        access_token = '1234567890'
        scope = 'user'
        token = self.generate_token(user, access_token, scope)
        self.assertTrue(token.is_valid())
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token.token)
        # update user info
        user_url = reverse_lazy(
            'v1:api_user_resource', kwargs={'pk': user.pk})
        data = {
            'nickname': 'test_nickname',
            'gender': 1,
        }
        response = self.client.patch(user_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # check database
        user = TechUUser.objects.get()
        self.assertEqual(user.gender, data.get('gender'))
        self.assertEqual(user.nickname, data.get('nickname'))

    def test_retrive_user(self):
        self.assertEqual(TechUUser.objects.count(), 1)
        user = TechUUser.objects.get()
        self.assertTrue(user)
        # generate access token
        access_token = '1234567890'
        scope = 'user'
        token = self.generate_token(user, access_token, scope)
        self.assertTrue(token.is_valid())
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token.token)
        # check user info
        user_url = reverse_lazy(
            'v1:api_user_resource', kwargs={'pk': user.pk})
        response = self.client.get(user_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK) 
        self.assertEqual(
            response.data.get('username'), self.test_user.get('username'))
        self.assertEqual(
            response.data.get('mobile'), self.test_user.get('mobile'))




class XPlatformNotifyAPITestCase(LiveServerTestCase):
    def setUp(self):
        cache.clear()
        self.test_url = self.live_server_url + reverse('v1:api_xplatform_notify')

    def tearDown(self):
        cache.clear()

    def test_minimal_notify(self):
        import time
        body = {
            'accountId': '123',
            'opType': 1,
            'time': int(time.time())
        }
        response = self.client.post(self.test_url, head={}, body=body)
        # TODO : finish this unittest ?
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)
