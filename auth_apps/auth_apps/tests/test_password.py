import sys
import logging
import unittest
import requests
import urllib
from urlparse import urlparse, parse_qs

from test_common import (
    ApplicationClient, ApplicationHelper, client_password_encode
)


logger = logging.getLogger(__name__)
out_hdlr = logging.StreamHandler(sys.stdout)
out_hdlr.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
logger.addHandler(out_hdlr)
logger.setLevel(logging.DEBUG)

BASE_URL = u'https://localhost:5000'
ADMIN_USERNAME = u'admin'
ADMIN_PASSWORD = u'admin'
ADMIN_USER_PK = 1
# LOGIN_USERNAME = u'user1'
# LOGIN_PASSWORD = u'user1'
LOGIN_USERNAME = u'15911186897'
LOGIN_PASSWORD = u'980468'
LOGIN_USER_PK = 2


class TestPassword(unittest.TestCase):
    def setUp(self):
        self.base_url = BASE_URL
        self.client = ApplicationClient(self.base_url, ADMIN_USERNAME, ADMIN_PASSWORD)
        self.application_helper = ApplicationHelper(self.client, self.base_url)
        app_params = {
            u'name': u'test_application',
            u'client_type': u'confidential',
            u'authorization_grant_type': u'password',
            u'redirect_uris': u'https://baidu.com/',
        }
        # force add application
        self.app = self.application_helper.force_add_application(app_params)

    def tearDown(self):
        self.application_helper.delete_application(self.app)
        self.client.driver.close()

    # 1 Application Requests Access Token
    def _application_requests_access_token(self):
        url = self.base_url + '/oauth/token/'
        payload = {
            u'grant_type': u'password',
            u'identity': LOGIN_USERNAME,
            u'password': client_password_encode(LOGIN_PASSWORD),
        }
        r = requests.post(url, data=payload, auth=(
            self.app.get(u'client_id'), self.app.get(u'client_secret')
            ), verify=False)
        print r.content
        self.assertEqual(r.status_code, 200)
        token_info = r.json()
        logger.info(u'Get token info : {res}'.format(res=token_info))
        return token_info

    # 2 Application requests resource by using access token
    def _application_requests_resource(self, token_info, user_pk):
        url = self.base_url + '/accounts/resource/user/{pk}/'.format(
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

    # 3 Refresh Token
    def _application_revoke_token(self, token_info):
        url = self.base_url + '/oauth/revoke_token/'
        payload = {
            u'grant_type': u'password',
            u'refresh_token': token_info.get('refresh_token'),
            u'token': token_info.get('access_token'),
        }
        r = requests.post(url, data=payload, auth=(
            self.app.get(u'client_id'), self.app.get(u'client_secret')
            ), verify=False)
        self.assertEqual(r.status_code, 200)
        return True 

    def test_password(self):
        import time
        access_token_info = self._application_requests_access_token()
        time.sleep(5)
        self.assertTrue(access_token_info)
        user_info = self._application_requests_resource(
            access_token_info, LOGIN_USER_PK)
        self.assertTrue(user_info)
        res = self._application_revoke_token(access_token_info)
        self.assertTrue(res)


if __name__ == '__main__':
    unittest.main()
