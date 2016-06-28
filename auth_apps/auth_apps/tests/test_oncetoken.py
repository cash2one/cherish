import sys
import logging
import unittest
import requests
import os
import django
from django.conf import settings
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    # NOTICE : call django setting first to allow define models
    settings.configure(
        XPLATFORM_SERVICE = {
        'URL': 'https://dev.login.yunxiaoyuan.com',
        'APP_ID': '98008',
        'SERVER_KEY': 'C6F653399B9A15E053469A66',
        'CLIENT_KEY': '9852C11D7FF63FDE5732A4BA',
        'TIMEOUT': 3,
    })
    # Calling django.setup() is required for “standalone” Django usage
    django.setup()

from test_common import (
    ApplicationClient, ApplicationHelper, client_password_encode
)


from common.xplatform_service import xplatform_service

logger = logging.getLogger(__name__)
out_hdlr = logging.StreamHandler(sys.stdout)
out_hdlr.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
logger.addHandler(out_hdlr)
logger.setLevel(logging.DEBUG)

BASE_URL = u'https://localhost:5000'
AUTH_PROXY_URL = u'https://localhost:5001'
ADMIN_USERNAME = u'admin'
ADMIN_PASSWORD = u'admin'
ADMIN_USER_PK = 1
LOGIN_USER_NAME = u'18503008450'
LOGIN_PASSWORD = u'123456'
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

    def get_once_token(self):
        res = xplatform_service.backend_login(LOGIN_USER_NAME, LOGIN_PASSWORD)
        if res:
            return res.get(u'accountId'), res.get(u'onceToken')
        return None, None

    # 1 Application Requests Access Token
    def _application_requests_access_token(self):
        account_id, once_token = self.get_once_token()
        self.assertTrue(account_id and once_token)
        url = self.base_url + '/oauth/token/'
        payload = {
            u'grant_type': u'password',
            u'username': account_id,
            u'password': once_token,
        }
        r = requests.post(url, data=payload, auth=(
            self.app.get(u'client_id'), self.app.get(u'client_secret')
        ), verify=False)
        print r.content
        self.assertEqual(r.status_code, 200)
        token_info = r.json()
        logger.info(u'Get token info : {res}'.format(res=token_info))
        return token_info

    def test_password(self):
        import time
        access_token_info = self._application_requests_access_token()
        time.sleep(5)
        self.assertTrue(access_token_info)

if __name__ == '__main__':
    unittest.main()
