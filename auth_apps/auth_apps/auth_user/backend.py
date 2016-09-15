# coding: utf-8
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.core.cache import cache

from common.xplatform_service import xplatform_service


class LoginPolicy(object):
    CACHE_KEY_PREFIX = 'LC-'
    LOGIN_COUNT = 3
    LOGIN_FLUSH_SECONDS = 3600

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
