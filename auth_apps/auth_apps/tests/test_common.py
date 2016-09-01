import logging
import hashlib
from contextlib import contextmanager
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

logger = logging.getLogger(__name__)


def client_password_encode(raw_password):
    FRONTEND_SALT = 'cloud_homework-'
    return hashlib.md5(FRONTEND_SALT + raw_password).hexdigest()


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
        name_elem = self.driver.find_element_by_name('identity')
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
         'authorization_grant_type': one of [
            authorization-code, implicit, password, client-credentials
         ],
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
        self._set_select_option(
            app_client_type_elem, application.get('client_type'))
        # set application authorization grant type
        app_grant_type_elem = cli.driver.find_element_by_name(
            'authorization_grant_type')
        self._set_select_option(
            app_grant_type_elem, application.get('authorization_grant_type'))
        # set application callback uri
        app_uri_elem = cli.driver.find_element_by_name('redirect_uris')
        app_uri_elem.send_keys(application.get('redirect_uris'))
        # get application client_id and client_secret
        client_id = cli.driver.find_element_by_name(
            'client_id').get_attribute('value')
        client_secret = cli.driver.find_element_by_name(
            'client_secret').get_attribute('value')
        application[u'client_id'] = client_id
        application[u'client_secret'] = client_secret
        # register confirm
        register_elem = cli.driver.find_element_by_id('id_save')
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
        # check application exist ?
        with self.client.user_context() as cli:
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
