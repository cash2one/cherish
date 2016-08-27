# -*- coding: utf-8 -*-

import time
import logging

import requests
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from auth_user.models import TechUUser
from custom_oauth2.models import TechUApplication

logger = logging.getLogger(__name__)

USER = {
    'username': 'user1',
    'password': 'user1'
}

APPLICATION = {
    'client_id': 'wvPgnn1d5zoRJPSMmyr106n5DV70fS95sgTjrh0z',
    'client_secret': 'l927kHhefalV2e4rBDOj2oPlOW6v92IjngIi2AYAoOd92OjOTlQhOSx1qWDmmmpUxvVzza05bES0GGDTAhBkCCmweemntbfuZ1hrJp5GRFzV13ZSHGpx2vc9E1ImJp2C',
    'redirect_uris': 'https://baidu.com/',
    'client_type': 'confidential',
    'authorization_grant_type': 'password',
    'name': 'test_application'
}


class TestUniqueToken(StaticLiveServerTestCase):

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
        super(TestUniqueToken, self).tearDown()

    def _application_requests_access_token(self):
        url = self.base_url + '/oauth/token/'
        payload = {
            'grant_type': 'password',
        }
        payload.update(**USER)
        r = requests.post(url, data=payload, auth=(
            APPLICATION.get('client_id'),
            APPLICATION.get('client_secret')), verify=False)
        self.assertEqual(r.status_code, 200)
        token_info = r.json()
        return token_info

    def test_unique_token(self):
        token_info = self._application_requests_access_token()
        self.assertTrue(token_info)
        self.assertNotEqual(token_info.get('access_token'),
                            token_info.get('refresh_token'))
        twice_token_info = self._application_requests_access_token()
        self.assertTrue(twice_token_info)
        self.assertEqual(token_info.get('access_token'),
                         twice_token_info.get('access_token'))
