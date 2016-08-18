# -*- coding: utf-8 -*-

import os
import sys
import urllib
import logging
from urlparse import urlparse, parse_qs

import requests
import django
from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from auth_user.models import TechUUser
from custom_oauth2.models import TechUApplication
from common.xplatform_service import xplatform_service


sys.path.append(os.path.abspath(os.path.dirname(__name__) + '..'))

if not os.getenv('DJANGO_SETTINGS_MODULE'):
    # NOTICE : call django setting first to allow define models
    settings.configure(
        XPLATFORM_SERVICE={
            'URL': 'https://dev.login.yunxiaoyuan.com',
            'APP_ID': '98008',
            'SERVER_KEY': 'C6F653399B9A15E053469A66',
            'CLIENT_KEY': '9852C11D7FF63FDE5732A4BA',
            'TIMEOUT': 3,
        }
    )
    # Calling django.setup() is required for "standalone" Django usage
    django.setup()

logger = logging.getLogger(__name__)

USER = {
    'username': 'user1',
    'password': 'user1'
}

XPLATFORM_USER = {
    'username': '18503008450',
    'raw_password': '123456'
}

APPLICATION = {
    'client_id': 'wvPgnn1d5zoRJPSMmyr106n5DV70fS95sgTjrh0z',
    'client_secret': 'l927kHhefalV2e4rBDOj2oPlOW6v92IjngIi2AYAoOd92OjOTlQhOSx1qWDmmmpUxvVzza05bES0GGDTAhBkCCmweemntbfuZ1hrJp5GRFzV13ZSHGpx2vc9E1ImJp2C',
    'redirect_uris': 'https://baidu.com/',
    'client_type': 'confidential',
    'authorization_grant_type': 'password',
    'name': 'test_application'
}


class TestOnceToken(StaticLiveServerTestCase):

    def setUp(self):
        self.base_url = self.live_server_url
        self.user = TechUUser.objects.create_user(**USER)
        data = {}
        data.update(APPLICATION)
        data.update({
            'user': self.user
        })
        self.app = TechUApplication.objects.create(**data)

    def tearDown(self):
        super(TestOnceToken, self).tearDown()

    def _get_once_token(self):
        res = xplatform_service.backend_login(**XPLATFORM_USER)
        if res:
            return res.get('accountId'), res.get('onceToken')
        return None, None

    # 1 Application Requests Access Token
    def _application_requests_access_token(self):
        account_id, once_token = self._get_once_token()
        url = self.base_url + '/oauth/token/'
        payload = {
            'grant_type': 'password',
            'username': account_id,
            'password': once_token
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

    def test_once_token(self):
        access_token_info = self._application_requests_access_token()
        self.assertTrue(access_token_info)
        user_info = self._application_requests_resource(access_token_info)
        self.assertTrue(user_info)
