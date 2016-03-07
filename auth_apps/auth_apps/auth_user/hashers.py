# coding: utf-8
from __future__ import unicode_literals

import hashlib
from collections import OrderedDict

from django.utils.translation import ugettext_noop as _
from django.utils.encoding import force_bytes
from django.utils.crypto import constant_time_compare
from django.contrib.auth.hashers import BasePasswordHasher, mask_hash


class TechUPasswordHasher(BasePasswordHasher):
    """                                                                         
    The Salted MD5 password hashing algorithm (not recommended)                 
    """                                                                         
    algorithm = "md5"
    backend_salt = 'yzy-'                                                         
                                                                                
    def encode(self, password, salt):
        assert password is not None
        assert salt and '$' not in salt
        hash = hashlib.md5(force_bytes(salt + password)).hexdigest()
        return "%s$%s$%s" % (self.algorithm, salt, hash)
                                                                                
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

    def salt(self):
        """
        Generates a cryptographically secure nonce salt in ASCII                
        """
        return self.backend_salt + user_salt
