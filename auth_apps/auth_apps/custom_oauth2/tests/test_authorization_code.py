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
    'authorization_grant_type': 'authorization-code',
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
    def _authorization_code_link(self):
        url = self.base_url + '/oauth/authorize/'
        params = {
            'state': 'test_state',
            'response_type': 'code',
            'client_id': APPLICATION.get('client_id')
        }
        auth_link = url + '?' + urllib.urlencode(params)
        logger.info('Authorization Code Link : {link}'.format(link=auth_link))
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
            'state': 'test_state',
            'response_type': 'code'
        }
        r = self.s.post(r.url, data=data, cookies=r.cookies, allow_redirects=False)
        self.assertEqual(r.status_code, 302)
        callback_uri = r.headers.get('Location')
        logger.info('Redirect to callback URI : {link}'.format(link=callback_uri))
        return callback_uri

    # 3 Application Receives Authorization Code
    def _application_receives_authorization_code(self, callback_uri):
        app_callback = urlparse(APPLICATION.get('redirect_uris'))
        callback = urlparse(callback_uri)
        self.assertEqual(callback.scheme, app_callback.scheme)
        # get grant code
        grant_code = parse_qs(callback.query).get('code')[0]
        logger.info('Authorization Code : {code}'.format(code=grant_code))
        return grant_code

    # 4 Application Requests Access Token
    def _application_requests_access_token(self, code):
        url = self.base_url + '/oauth/token/'
        payload = {
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': APPLICATION.get('redirect_uris'),
            'scope': 'user group'
        }
        r = self.s.post(url, data=payload, auth=(
            APPLICATION.get('client_id'),
            APPLICATION.get('client_secret')), verify=False)
        self.assertEqual(r.status_code, 200)
        token_info = r.json()
        logger.info('Get user info : {res}'.format(res=token_info))
        return token_info

    # Application requests resource by using access token
    def _application_requests_resource(self, token_info):
        url = self.base_url + '/accounts/api/v1/user/{pk}/'.format(pk=self.user.pk)
        headers = {
            'Authorization': '{token_type} {access_token}'.format(
                token_type=token_info.get('token_type'),
                access_token=token_info.get('access_token')
            )
        }
        r = requests.get(url, headers=headers, verify=False)
        self.assertEqual(r.status_code, 200)
        user_info = r.json()
        logger.info(u'Get user info : {res}'.format(res=user_info))
        return user_info

    def test_authorization_code(self):
        auth_link = self._authorization_code_link()
        self.assertTrue(auth_link)
        callback_uri = self._user_authorizes_application(auth_link)
        self.assertTrue(callback_uri)
        code = self._application_receives_authorization_code(callback_uri)
        self.assertTrue(code)
        access_token_info = self._application_requests_access_token(code)
        self.assertTrue(access_token_info)
        user_info = self._application_requests_resource(
            access_token_info)
        self.assertTrue(user_info)
