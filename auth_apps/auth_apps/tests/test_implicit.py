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

BASE_URL = u'http://localhost:5000'
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
            u'authorization_grant_type': u'implicit',
            u'redirect_uris': u'https://baidu.com/',  # get grant code callback
        }
        # force add application
        self.app = self.application_helper.force_add_application(app_params)

    def tearDown(self):
        self.application_helper.delete_application(self.app)
        self.client.driver.close()

    # 1 Implicit Authorization Link
    def _implicit_authorization_link(self):
        url = self.base_url + '/oauth/authorize/'
        params = {
            u'response_type': u'token',
            u'client_id': self.app.get('client_id'),
        }
        auth_link = url + '?' + urllib.urlencode(params)
        logger.info(u'Implicit Authorization Link : {link}'.format(link=auth_link))
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

    # 3 User-agent Receives Access Token with Redirect URI
    # 4 Application Sends Access Token Extraction Script
    # 5 Access Token Passed to Application
    def _application_get_access_token(self, callback_uri):
        callback = urlparse(callback_uri)
        # get grant code
        token_info = parse_qs(callback.fragment)
        logger.info(u'Access Token: {token}'.format(token=token_info))
        return token_info 

    # Application requests resource by using access token
    def _application_requests_resource(self, token_info, user_pk):
        url = self.base_url + '/accounts/api/v1/user/{pk}/'.format(
            pk=user_pk)
        headers = {
            u'Authorization': u'{token_type} {access_token}'.format(
                token_type=token_info.get(u'token_type')[0],
                access_token=token_info.get(u'access_token')[0]
            )
        }
        r = requests.get(url, headers=headers, verify=False)
        self.assertEqual(r.status_code, 200)
        user_info = r.json()
        logger.info(u'Get user info : {res}'.format(res=user_info))
        return user_info

    def test_authorization_code(self):
        import time
        auth_link = self._implicit_authorization_link()
        time.sleep(5)
        self.assertTrue(auth_link)
        callback_uri = self._user_authorizes_application(auth_link)
        time.sleep(5)
        self.assertTrue(callback_uri)
        token_info = self._application_get_access_token(callback_uri)
        time.sleep(5)
        self.assertTrue(token_info)
        user_info = self._application_requests_resource(
            token_info, USER_PK)
        self.assertTrue(user_info)

if __name__ == '__main__':
    unittest.main()
