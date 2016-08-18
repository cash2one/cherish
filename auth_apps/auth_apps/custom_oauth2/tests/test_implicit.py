# -*- coding: utf-8 -*-

import urllib
import logging
from urlparse import urlparse, parse_qs

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
    'authorization_grant_type': 'implicit',
    'name': 'test_application'
}


class TestAuthorizationCode(StaticLiveServerTestCase):

    def setUp(self):
        self.base_url = self.live_server_url
        self.user = TechUUser.objects.create_user(**USER)
        self.s = requests.session()
        data = {}
        data.update(APPLICATION)
        data.update({
            'user': self.user
        })
        self.app = TechUApplication.objects.create(**data)

    def tearDown(self):
        super(TestAuthorizationCode, self).tearDown()

    # 1 Authorization Code Link
    def _implicit_authorization_link(self):
        url = self.base_url + '/oauth/authorize/'
        params = {
            'response_type': 'token',
            'client_id': APPLICATION.get('client_id')
        }
        auth_link = url + '?' + urllib.urlencode(params)
        logger.info('Implicit Authorization Link : {link}'.format(link=auth_link))
        return auth_link

    # 2 User Authorizes Application
    def _user_authorizes_application(self, auth_link):
        login_url = self.base_url + '/accounts/login/'
        r = self.s.get(login_url)
        csrf_token = r.cookies['csrftoken']
        self.assertTrue(csrf_token)
        data = {
            'identity': USER.get('username'),
            'password': USER.get('password'),
            'csrfmiddlewaretoken': csrf_token,
            'next': ''
        }
        r = self.s.post(login_url, data=data, cookies=r.cookies)
        self.assertEqual(r.status_code, 200)
        r = self.s.get(auth_link)
        self.assertEqual(r.status_code, 200)
        csrf_token = r.cookies['csrftoken']
        data = {
            'allow': 'Authorize',
            'csrfmiddlewaretoken': csrf_token,
            'redirect_uri': APPLICATION.get('redirect_uris'),
            'scope': 'user group',
            'client_id': APPLICATION.get('client_id'),
            'state': '',
            'response_type': 'token'
        }
        r = self.s.post(r.url, data=data, cookies=r.cookies, allow_redirects=False)
        self.assertEqual(r.status_code, 302)
        callback_uri = r.headers.get('Location')
        logger.info('Redirect to callback URI : {link}'.format(link=callback_uri))
        return callback_uri

    # 3 Application Receives Authorization Code
    def _application_get_access_token(self, callback_uri):
        callback = urlparse(callback_uri)
        # get grant code
        token_info = parse_qs(callback.fragment)
        logger.info('Access Token: {code}'.format(code=token_info))
        return token_info

    # Application requests resource by using access token
    def _application_requests_resource(self, token_info):
        url = self.base_url + '/accounts/api/v1/user/{pk}/'.format(pk=self.user.pk)
        headers = {
            'Authorization': '{token_type} {access_token}'.format(
                token_type=token_info.get('token_type')[0],
                access_token=token_info.get('access_token')[0]
            )
        }
        r = requests.get(url, headers=headers, verify=False)
        self.assertEqual(r.status_code, 200)
        user_info = r.json()
        logger.info('Get user info : {res}'.format(res=user_info))
        return user_info

    def test_authorization_code(self):
        auth_link = self._implicit_authorization_link()
        self.assertTrue(auth_link)
        callback_uri = self._user_authorizes_application(auth_link)
        self.assertTrue(callback_uri)
        token_info = self._application_get_access_token(callback_uri)
        self.assertTrue(token_info)
        user_info = self._application_requests_resource(
            token_info)
        self.assertTrue(user_info)
