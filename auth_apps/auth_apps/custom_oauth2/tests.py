# -*- coding: utf-8 -*-

import time
import logging
from collections import namedtuple

import requests
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

logger = logging.getLogger(__name__)

User = namedtuple('User', ['pk', 'username', 'password'])
App = namedtuple('App', ['name', 'client_type', 'authorization_grant_type', 'redirect_uris'])
Client = namedtuple('Client', ['client_id', 'client_secret'])


class TestUniqueToken(StaticLiveServerTestCase):

    fixtures = ['user.json', 'auth.json', 'application.json']

    def setUp(self):
        self.base_url = self.live_server_url
        self.admin = User(1, 'admin', 'admin')
        self.tuser = User(2, 'user1', 'user1')
        self.app = App('test_application', 'confidential', 'password', 'https://baidu.com/')
        self.client = Client(
            'wvPgnn1d5zoRJPSMmyr106n5DV70fS95sgTjrh0z',
            'l927kHhefalV2e4rBDOj2oPlOW6v92IjngIi2AYAoOd92OjOTlQhOSx1qWDmmmpUxvVzza05bES0GGDTAhBkCCmweemntbfuZ1hrJp5GRFzV13ZSHGpx2vc9E1ImJp2C'
        )

    def tearDown(self):
        pass

    def _application_requests_access_token(self):
        url = self.base_url + '/oauth/token/'
        payload = {
            'grant_type': 'password',
        }
        payload.update(vars(self.tuser))
        r = requests.post(url, data=payload, auth=(
            vars(self.client).get('client_id'),
            vars(self.client).get('client_secret')), verify=False)
        self.assertEqual(r.status_code, 200)
        token_info = r.json()
        return token_info

    def test_unique_token(self):
        token_info = self._application_requests_access_token()
        time.sleep(2)
        self.assertTrue(token_info)
        twice_token_info = self._application_requests_access_token()
        self.assertTrue(twice_token_info)
        self.assertEqual(token_info.get('access_token'),
                         twice_token_info.get('access_token'))
