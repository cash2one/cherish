# -*- coding: utf-8 -*-

import logging

import requests
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from django.contrib.auth.models import Group
from auth_user.models import TechUUser
from custom_oauth2.models import TechUApplication

logger = logging.getLogger(__name__)

USER = {
    'username': 'user1',
    'password': 'user1',
    'mobile': 13800138000
}

APPLICATION = {
    'client_id': 'wvPgnn1d5zoRJPSMmyr106n5DV70fS95sgTjrh0z',
    'client_secret': 'l927kHhefalV2e4rBDOj2oPlOW6v92IjngIi2AYAoOd92OjOTlQhOSx1qWDmmmpUxvVzza05bES0GGDTAhBkCCmweemntbfuZ1hrJp5GRFzV13ZSHGpx2vc9E1ImJp2C',
    'redirect_uris': 'https://baidu.com/',
    'client_type': 'confidential',
    'authorization_grant_type': 'password',
    'name': 'test_application'
}


class TestPassword(StaticLiveServerTestCase):

    def setUp(self):
        self.base_url = self.live_server_url
        self.user = TechUUser.objects.create_user(**USER)
        # add user groups for test
        self.group = Group.objects.create(**{'name': 'test_group'})
        self.user.groups.add(self.group)
        data = {}
        data.update(APPLICATION)
        data.update({
            'user': self.user
        })
        self.app = TechUApplication.objects.create(**data)

    def tearDown(self):
        super(TestPassword, self).tearDown()

    # 1 Application Requests Access Token
    def _application_requests_access_token(self):
        url = self.base_url + '/oauth/token/'
        payload = {
            'grant_type': 'password',
        }
        payload.update(USER)
        r = requests.post(url, data=payload, auth=(
            APPLICATION.get('client_id'),
            APPLICATION.get('client_secret')), verify=False)
        self.assertEqual(r.status_code, 200)
        token_info = r.json()
        logger.info('Get token info : {res}'.format(res=token_info))
        return token_info

    # 2 Application requests resource by using access token
    def _application_requests_resource(self, token_info):
        url = self.base_url + '/accounts/api/v1/user/{pk}/'.format(
            pk=self.user.pk)
        headers = {
            'Authorization': '{token_type} {access_token}'.format(
                token_type=token_info.get('token_type'),
                access_token=token_info.get('access_token')
            )
        }
        r = requests.get(url, headers=headers, verify=False)
        self.assertEqual(r.status_code, 200)
        user_info = r.json()
        logger.info('Get user info : {res}'.format(res=user_info))
        return user_info

    # 3 Revoke Token
    def _application_revoke_token(self, token_info):
        url = self.base_url + '/oauth/revoke_token/'
        payload = {
            'grant_type': 'password',
            'refresh_token': token_info.get('refresh_token'),
            'token': token_info.get('access_token')
        }
        r = requests.post(url, data=payload, auth=(
            APPLICATION.get('client_id'),
            APPLICATION.get('client_secret')), verify=False)
        self.assertEqual(r.status_code, 200)
        return True

    def test_password(self):
        access_token_info = self._application_requests_access_token()
        self.assertTrue(access_token_info)
        self.assertEqual(access_token_info.get('user_id'), self.user.pk)
        self.assertEqual(access_token_info.get('user_mobile'), self.user.mobile)
        self.assertEqual(access_token_info.get('user_username'), self.user.username)
        self.assertTrue(isinstance(access_token_info.get('groups'), list))
        self.assertEqual(access_token_info.get('groups'), [self.group.name])
        user_info = self._application_requests_resource(access_token_info)
        self.assertTrue(user_info)
        res = self._application_revoke_token(access_token_info)
        self.assertTrue(res)
