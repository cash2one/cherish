# coding: utf-8
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.core.cache import cache


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
