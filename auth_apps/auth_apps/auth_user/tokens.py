# coding: utf-8
import string
import random
import logging

from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from .validators import validate_mobile_code
from .backend import LoginPolicy

logger = logging.getLogger(__name__)


class EmailTokenGenerator(PasswordResetTokenGenerator):
    # override method
    def check_token(self, user, token):
        res = super(EmailTokenGenerator, self).check_token(user, token)
        if res:
            # reset login constraint
            LoginPolicy.flush_constraint(user)
        return res


class MobileTokenGenerator(object):
    CACHE_KEY_PREFIX = 'MTG-'
    DEFAULT_CODE_LENGTH = 6
    DEFAULT_TIMEOUT_SECONDS = 180
    """
    Strategy object used to generate and check tokens for the password
    reset mechanism.
    """
    def __init__(self):
        self.timeout = self.DEFAULT_TIMEOUT_SECONDS

    def get_key(self, obj):
        return self.CACHE_KEY_PREFIX + unicode(obj)

    def make_token(self, obj):
        """
        Returns a token that can be used once to do a password reset
        for the given user.
        """
        key = self.get_key(obj)
        return cache.get_or_set(key, self._random_code(), self.timeout)

    def check_token(self, obj, token):
        if not self._is_code(token):
            logger.debug('mobile token invalid')
            return False
        key = self.get_key(obj)
        _token = cache.get(key)
        if _token == token:
            cache.delete(key)
            return True
        return False

    def _random_code(self, length=DEFAULT_CODE_LENGTH):
        return ''.join(random.choice(string.digits) for _ in range(length))

    def _is_code(self, code):
        # check all numbers, and DEFAULT_CODE_LENGTH
        try:
            return validate_mobile_code(code)
        except:
            return False


class UserMobileTokenGenerator(MobileTokenGenerator):
    CACHE_KEY_PREFIX = 'UMTG-'

    def get_key(self, obj):
        assert(isinstance(obj, get_user_model()))
        return self.CACHE_KEY_PREFIX + unicode(obj.pk)

    def check_token(self, obj, token):
        check_res = super(
            UserMobileTokenGenerator, self).check_token(obj, token)
        if check_res:
            # reset login constraint
            LoginPolicy.flush_constraint(user=obj)
        return check_res

# export generators
general_mobile_token_generator = MobileTokenGenerator()
user_mobile_token_generator = UserMobileTokenGenerator()
email_token_generator = EmailTokenGenerator()
