from __future__ import unicode_literals

from django.db import models
from django.core import validators
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


class TechUUser(AbstractUser):
    BACKEND_SALT = 'yzy-'
    # NOTICE: required either email or mobile, see UserRegisterForm for detail.

    birth_date = models.DateField(_('Birthday'), null=True, blank=True)
    qq = models.BigIntegerField(_('QQ'), null=True, blank=True)
    remark = models.CharField(
        _('Remark'), max_length=256, null=True, blank=True)
    mobile = models.CharField(
        _('Mobile'), max_length=32,
        validators=[
            validators.RegexValidator(r'^[\d]+$',
                                      _('Enter a valid mobile number. '
                                        'This value may contain only numbers'),
                                      'invalid'),
        ],
        null=True, blank=True)
    phone = models.CharField(_('Phone'), max_length=32, 
        validators=[
            validators.RegexValidator(r'^[\d-]+$',
                                      _('Enter a valid phone number. '
                                        'This value may contain only numbers '
                                        'and - characters'), 'invalid'),
        ],
        null=True, blank=True)
    address = models.CharField(
        _('Address'), max_length=512, null=True, blank=True)
    
    def set_password(self, raw_password):
        self.password = make_password(
            raw_password, salt = self.BACKEND_SALT + self.username)

    def set_unusable_password(self):
        # Sets a value that will never be a valid hash
        self.password = make_password(
            None, salt = self.BACKEND_SALT + self.username)

