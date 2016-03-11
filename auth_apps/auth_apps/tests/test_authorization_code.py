import sys
import logging
import unittest
import requests
import urllib
from urlparse import urlparse, parse_qs
from contextlib import contextmanager
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException


logger = logging.getLogger(__name__)
out_hdlr = logging.StreamHandler(sys.stdout)
out_hdlr.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
logger.addHandler(out_hdlr)
logger.setLevel(logging.DEBUG)

BASE_URL = u'https://localhost:5000'
USERNAME = u'admin'
PASSWORD = u'admin'
USER_PK = 1

class ApplicationClient(object):
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.driver = webdriver.Firefox()
        self._is_login = False

    def user_login(self, passive=False):
        if self._is_login:
            return
        # passive means we are already in the login page
        if not passive:
            self.driver.get(self.base_url + '/accounts/login/')
        name_elem = self.driver.find_element_by_name('username')
        pwd_elem = self.driver.find_element_by_name('password')
        name_elem.send_keys(self.username)
        pwd_elem.send_keys(self.password)
        login_elem = self.driver.find_element_by_class_name('btn-primary')
        login_elem.click()
        # login finished
        self._is_login = True 

    def user_logout(self):
        if not self._is_login:
            return
        self.driver.get(self.base_url + '/accounts/logout/')
        self._is_login = False

    def user_is_login(self):
        return self._is_login

    def confirm(self, allow=True):
        try:
            confirm_elem = self.driver.find_element_by_name('allow')
        except NoSuchElementException:
            return False
        if confirm_elem and allow:
            confirm_elem.click()
            return True
        return False

    @contextmanager
    def user_context(self):
        self.user_login()
        yield self 
        self.user_logout()
    

class ApplicationHelper(object):

    def __init__(self, client, base_url):
        self.base_url = base_url
        self.client = client

    # return True if selected
    def _set_select_option(self, select_elem, dst_value):
        for option in select_elem.find_elements_by_tag_name('option'):
            if option.get_attribute('value') == dst_value:
                option.click()
                return True
        return False


    """
     application : {
         'name': app_name,
         'authorization_grant_type': one of [authorization-code, implicit, password, client-credentials],
         'client_type': one of [confidential, public]
         'redirect_uris': app callback uri
     }
    """
    def _add_application(self, application):
        cli = self.client
        # register new application
        cli.driver.get(self.base_url + '/oauth/applications/register/')
        # set application name
        app_name_elem = cli.driver.find_element_by_name('name')
        app_name_elem.send_keys(application.get('name'))
        # set application client type
        app_client_type_elem = cli.driver.find_element_by_name('client_type')
        self._set_select_option(app_client_type_elem, application.get('client_type'))
        # set application authorization grant type
        app_grant_type_elem = cli.driver.find_element_by_name('authorization_grant_type')
        self._set_select_option(app_grant_type_elem, application.get('authorization_grant_type'))
        # set application callback uri
        app_uri_elem = cli.driver.find_element_by_name('redirect_uris')
        app_uri_elem.send_keys(application.get('redirect_uris'))
        # get application client_id and client_secret
        client_id = cli.driver.find_element_by_name('client_id').get_attribute('value')
        client_secret = cli.driver.find_element_by_name('client_secret').get_attribute('value')
        application[u'client_id'] = client_id
        application[u'client_secret'] = client_secret
        # register confirm
        register_elem = cli.driver.find_element_by_tag_name('button')
        register_elem.click()
        logger.info('Create new application : {app}'.format(app=application))
        return application

    def _check_application(self, application):
        app_name = application.get('name')
        assert(app_name)
        cli = self.client
        # list all applications belong to current login user
        cli.driver.get(self.base_url + '/oauth/applications/')
        # find the check one
        try:
            app_elem = cli.driver.find_element_by_link_text(app_name)
        except NoSuchElementException:
            app_elem = None
        return (app_elem is not None)

    def force_add_application(self, application):
        with self.client.user_context() as cli:
            # check application exist ?
            if self._check_application(application):
                self._delete_application(application)
            return self._add_application(application)

    # return True if deleted
    def _delete_application(self, application):
        app_name = application.get('name')
        assert(app_name)
        cli = self.client
        # list all applications belong to current login user
        cli.driver.get(self.base_url + '/oauth/applications/')
        # find the delete one
        app_elem = cli.driver.find_element_by_link_text(app_name)
        if not app_elem:
            logger.error('cannot find app: {name}'.format(name=app_name))
            return False
        app_url = app_elem.get_attribute('href')
        cli.driver.get(app_url + 'delete/')
        # find delete confirm button
        delete_elem = cli.driver.find_element_by_name('allow')
        assert(delete_elem)
        delete_elem.click()
        return True

    def delete_application(self, application):
        with self.client.user_context() as cli:
            self._delete_application(application)


class TestAuthorizationCode(unittest.TestCase):
    def setUp(self):
        self.base_url = BASE_URL
        self.client = ApplicationClient(self.base_url, USERNAME, PASSWORD)
        self.application_helper = ApplicationHelper(self.client, self.base_url)
        app_params = {
            u'name': u'test_application',
            u'client_type': u'confidential',
            u'authorization_grant_type': u'authorization-code',
            u'redirect_uris': u'https://baidu.com/', # get grant code callback
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
        logger.info(u'Redirect to callback URI : {link}'.format(link=callback_uri))
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
            u'redirect_uri': u'https://baidu.com/', # get access token callback
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
        url = self.base_url + '/accounts/resource/user/{pk}/'.format(pk=user_pk)
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
        user_info = self._application_requests_resource(access_token_info, USER_PK)
        self.assertTrue(user_info)


if __name__ == '__main__':
    unittest.main()

