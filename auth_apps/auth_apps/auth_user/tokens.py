# coding: utf-8
import string
import random

from django.core.cache import cache
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.conf import settings

from .backend import LoginPolicy


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
    DEFAULT_PASSWORD_RESET_TIMEOUT_SECONDS = 180
    """
    Strategy object used to generate and check tokens for the password
    reset mechanism.
    """
    def __init__(self):
        self.timeout = self.DEFAULT_PASSWORD_RESET_TIMEOUT_SECONDS

    def get_key(self, user):
        return self.CACHE_KEY_PREFIX + unicode(user.pk)

    def make_token(self, user):
        """
        Returns a token that can be used once to do a password reset
        for the given user.
        """
        return self._make_token(user)

    def check_token(self, user, token):
        key = self.get_key(user)
        user_token = cache.get(key)
        if user_token == token:
            cache.delete(key)
            # reset login constraint
            LoginPolicy.flush_constraint(user)
            return True
        return False

    def _make_token(self, user):
        key = self.get_key(user)
        return cache.get_or_set(key, self._random_code(), self.timeout)

    def _random_code(self, length=DEFAULT_CODE_LENGTH):
        return ''.join(random.choice(string.digits) for _ in range(length))


mobile_token_generator = MobileTokenGenerator()
email_token_generator = EmailTokenGenerator()
