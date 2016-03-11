# coding: utf-8
import string
import random

from django.core.cache import cache
from django.conf import settings


class PasswordResetCodeGenerator(object):
    DEFAULT_CODE_LENGTH = 6
    DEFAULT_PASSWORD_RESET_TIMEOUT_SECONDS = 180
    """
    Strategy object used to generate and check tokens for the password
    reset mechanism.
    """
    def __init__(self):
        self.timeout = self.DEFAULT_PASSWORD_RESET_TIMEOUT_SECONDS

    def make_token(self, user):
        """
        Returns a token that can be used once to do a password reset
        for the given user.
        """
        return self._make_token(user)

    def check_token(self, user, token):
        user_token = cache.get(user)
        if user_token == token:
            cache.delete(user)
            return True
        return False

    def _make_token(self, user):
        return cache.get_or_set(user, self._random_code(), self.timeout)

    def _random_code(self, length=DEFAULT_CODE_LENGTH):
        return ''.join(random.choice(string.digits) for _ in range(length))


mobile_token_generator = PasswordResetCodeGenerator()
