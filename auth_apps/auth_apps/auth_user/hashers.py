from __future__ import unicode_literals

import hashlib
from collections import OrderedDict
from django.utils.encoding import force_bytes
from django.utils.crypto import constant_time_compare
from django.utils.translation import ugettext_noop as _
from django.contrib.auth.hashers import BasePasswordHasher, mask_hash
from django.conf import settings


class TechUPasswordHasher(BasePasswordHasher):
    """
    The twice Salted MD5 password hashing algorithm (TechU specific)
    """
    algorithm = "techu"
    FRONTEND_SALT = settings.TECHU_FRONTEND_SALT 

    def encode(self, password, salt):
        assert password is not None
        assert salt and '$' not in salt
        front_password = hashlib.md5(
            force_bytes(self.FRONTEND_SALT + password)
        ).hexdigest()
        hash = hashlib.md5(force_bytes(salt + front_password)).hexdigest()
        return "%s$%s$%s" % (self.algorithm, salt, hash)

    @classmethod
    def import_password(cls, hashed_password, salt):
        return "%s$%s$%s" % (cls.algorithm, salt, hashed_password)

    def verify(self, password, encoded):
        algorithm, salt, hash = encoded.split('$', 2)
        assert algorithm == self.algorithm
        encoded_2 = self.encode(password, salt)
        return constant_time_compare(encoded, encoded_2)

    def safe_summary(self, encoded):
        algorithm, salt, hash = encoded.split('$', 2)
        assert algorithm == self.algorithm
        return OrderedDict([
            (_('algorithm'), algorithm),
            (_('salt'), mask_hash(salt, show=2)),
            (_('hash'), mask_hash(hash)),
        ])
