# coding: utf-8
from __future__ import unicode_literals

import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.cache import cache
from django.conf import settings

from common.xplatform_service import xplatform_service

logger = logging.getLogger(__name__)


class LoginPolicy(object):
    CACHE_KEY_PREFIX = 'LC-'
    LOGIN_COUNT = settings.POLICY_LOGIN_COUNT or 5
    LOGIN_FLUSH_SECONDS = settings.POLICY_LOGIN_FLUSH_SECONDS or 3600

    class LoginConstraintException(Exception):
        pass

    @classmethod
    def get_key(cls, user):
        return cls.CACHE_KEY_PREFIX + unicode(user.pk)

    @classmethod
    def do_constraint(cls, user):
        key = cls.get_key(user)
        # TODO: atomic ?
        count = cache.get_or_set(key, 1, cls.LOGIN_FLUSH_SECONDS)
        if count <= cls.LOGIN_COUNT:
            cache.incr(key)
            return False
        # return true if login limited
        return True

    @classmethod
    def flush_constraint(cls, user):
        key = cls.get_key(user)
        cache.delete(key)

    @classmethod
    def limited(cls, user):
        key = cls.get_key(user)
        count = cache.get(key)
        if count:
            return (count > cls.LOGIN_COUNT)
        return False


class TechUBackend(object):

    @staticmethod
    def _get_user_by_email(identity):
        return get_user_model().objects.get(email=identity)

    @staticmethod
    def _get_user_by_mobile(identity):
        return get_user_model().objects.get(mobile=identity)

    @staticmethod
    def _get_user_by_username(identity):
        return get_user_model().objects.get(username=identity)

    def _try_auth(self, identity, password, get_user_func):
        UserModel = get_user_model()
        try:
            user = get_user_func(identity)
            if LoginPolicy.limited(user):
                raise LoginPolicy.LoginConstraintException()
            if user.check_password(password):
                LoginPolicy.flush_constraint(user)
                return user
            elif LoginPolicy.do_constraint(user):
                # login constraint
                raise LoginPolicy.LoginConstraintException()
            return None
        except UserModel.DoesNotExist:
            return None

    def authenticate(self, identity=None, password=None, request=None):
        logger.debug('[{cls}] authenticate'.format(cls=self.__class__.__name__))
        user = self._try_auth(identity, password, self._get_user_by_email)
        if user:
            return user
        user = self._try_auth(identity, password, self._get_user_by_mobile)
        if user:
            return user
        user = self._try_auth(identity, password, self._get_user_by_username)
        if user:
            return user
        return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None


class XPlatformBackend(object):

    # Create a User object if not already in the database?
    create_unknown_user = True

    def authenticate(self, identity=None, password=None, request=None):
        logger.debug('[{cls}] authenticate'.format(cls=self.__class__.__name__))
        if not identity:
            return
        user = None
        identity = self.clean_username(identity)
        res = xplatform_service.backend_login(identity, password)
        if res:
            UserModel = get_user_model()
            # login success
            if self.create_unknown_user:
                user, created = UserModel._default_manager.get_or_create_techu_user(**{
                    UserModel.get_identity_field(identity): identity,
                    'password': password,
                    'context': res,
                    'source': UserModel.USER_SOURCE.XPLATFORM
                })
                if created:
                    user = self.configure_user(user)
                else:
                    if user.USER_SOURCE.ONCE_XPLATFORM == user.source:
                        user.update_password(password)
                        user.source = user.USER_SOURCE.XPLATFORM
                        user.save()
            else:
                try:
                    user = UserModel._default_manager.get_by_natural_key(identity)
                except UserModel.DoesNotExist:
                    pass
        return user

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None

    def clean_username(self, username):
        """
        Performs any cleaning on the "username" prior to using it to get or
        create the user object.  Returns the cleaned username.

        By default, returns the username unchanged.
        """
        return username

    def configure_user(self, user):
        """
        Configures a user after creation and returns the updated user.

        By default, returns the user unmodified.
        """
        return user


class XPlatformOnceTokenBackend(object):

    def authenticate(self, identity=None, password=None, request=None):
        logger.debug('[{cls}] authenticate'.format(cls=self.__class__.__name__))
        user = None
        # check account_id
        try:
            account_id, once_token = int(identity), password
        except ValueError:
            return user
        user_info = xplatform_service.backend_verify_get_account_info(
            account_id, once_token)
        if user_info:
            UserModel = get_user_model()
            # login success
            identity = user_info.get(u'accountName') or user_info.get(u'mobilePhone')
            logger.debug('identity: {i}'.format(i=identity))
            user, created = UserModel._default_manager.get_or_create_techu_user(**{
                UserModel.get_identity_field(identity): identity,
                'password': None,
                'context': user_info,
                'source': UserModel.USER_SOURCE.ONCE_XPLATFORM
            })
        return user

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None


class AdminBackend(ModelBackend):
    # override
    def authenticate(self, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        # NOTICE : can only use 'username' to login admin site
        try:
            user = UserModel._default_manager.get_by_natural_key(username)
            if user.check_password(password) and user.is_active and user.is_staff:
                return user
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            # NOTICE : change to use 'update_password' to prevent extra signal sends from 'set_password'
            UserModel().update_password(password)

