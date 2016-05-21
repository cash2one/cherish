import sys
import logging
import unittest
import requests
import urllib
from urlparse import urlparse, parse_qs

from test_common import ApplicationClient, ApplicationHelper


logger = logging.getLogger(__name__)
out_hdlr = logging.StreamHandler(sys.stdout)
out_hdlr.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
logger.addHandler(out_hdlr)
logger.setLevel(logging.DEBUG)

BASE_URL = u'https://localhost:5000'
USERNAME = u'admin'
PASSWORD = u'admin'
USER_PK = 1


class TestAuthorizationCode(unittest.TestCase):
    def setUp(self):
        self.base_url = BASE_URL
        self.client = ApplicationClient(self.base_url, USERNAME, PASSWORD)
        self.application_helper = ApplicationHelper(self.client, self.base_url)
        app_params = {
            u'name': u'test_application',
            u'client_type': u'confidential',
            u'authorization_grant_type': u'authorization-code',
            u'redirect_uris': u'https://baidu.com/',  # get grant code callback
        }
        # force add application
        self.app = self.application_helper.force_add_application(app_params)

    def tearDown(self):
        self.application_helper.delete_application(self.app)
        self.client.driver.close()

    # 1 Authorization Code Link
    def _authorization_code_link(self):
        url = self.base_url + '/oauth/authorize/'
        params = {
            u'state': u'test_state',
            u'response_type': u'code',
            u'client_id': self.app.get('client_id'),
        }
        auth_link = url + '?' + urllib.urlencode(params)
        logger.info(u'Authorization Code Link : {link}'.format(link=auth_link))
        return auth_link

    # 2 User Authorizes Application
    def _user_authorizes_application(self, auth_link):
        self.client.driver.get(auth_link)
        # redirect to user login page, user login
        self.client.user_login(passive=True)
        # user auhorizes scope page
        self.client.confirm(allow=True)
        # redirect user-agent to callback uri
        callback_uri = self.client.driver.current_url
        logger.info(u'Redirect to callback URI : {link}'.format(
            link=callback_uri))
        return callback_uri

    # 3 Application Receives Authorization Code
    def _application_receives_authorization_code(self, callback_uri):
        app_callback = urlparse(self.app.get('redirect_uris'))
        callback = urlparse(callback_uri)
        self.assertEqual(callback.scheme, app_callback.scheme)
        # get grant code
        grant_code = parse_qs(callback.query).get(u'code')[0]
        logger.info(u'Authorization Code : {code}'.format(code=grant_code))
        return grant_code

    # 4 Application Requests Access Token
    def _application_requests_access_token(self, code):
        url = self.base_url + '/oauth/token/'
        payload = {
            u'code': code,
            u'grant_type': u'authorization_code',
            # get access token callback
            u'redirect_uri': u'https://baidu.com/',
            u'scope': u'user group'
        }
        r = requests.post(url, data=payload, auth=(
            self.app.get(u'client_id'), self.app.get(u'client_secret')
            ), verify=False)
        self.assertEqual(r.status_code, 200)
        token_info = r.json()
        logger.info(u'Get token info : {res}'.format(res=token_info))
        return token_info

    # Application requests resource by using access token
    def _application_requests_resource(self, token_info, user_pk):
        url = self.base_url + '/accounts/api/v1/user/{pk}/'.format(
            pk=user_pk)
        headers = {
            u'Authorization': u'{token_type} {access_token}'.format(
                token_type=token_info.get(u'token_type'),
                access_token=token_info.get(u'access_token')
            )
        }
        r = requests.get(url, headers=headers, verify=False)
        self.assertEqual(r.status_code, 200)
        user_info = r.json()
        logger.info(u'Get user info : {res}'.format(res=user_info))
        return user_info

    def test_authorization_code(self):
        import time
        auth_link = self._authorization_code_link()
        time.sleep(5)
        self.assertTrue(auth_link)
        callback_uri = self._user_authorizes_application(auth_link)
        time.sleep(5)
        self.assertTrue(callback_uri)
        code = self._application_receives_authorization_code(callback_uri)
        time.sleep(5)
        self.assertTrue(code)
        access_token_info = self._application_requests_access_token(code)
        time.sleep(5)
        self.assertTrue(access_token_info)
        user_info = self._application_requests_resource(
            access_token_info, USER_PK)
        self.assertTrue(user_info)

if __name__ == '__main__':
    unittest.main()
