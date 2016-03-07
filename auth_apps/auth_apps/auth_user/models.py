from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


class TechUUser(AbstractUser):
    BACKEND_SALT = 'yzy-'

    birth_date = models.DateField(
        help_text=_('Birthday'), blank=True, null=True)
    qq = models.BigIntegerField(
        help_text=_('QQ'), default=0, blank=True, null=True)
    remark = models.CharField(
        help_text=_('Remark'), max_length=256, 
        default='', blank=True, null=True)
    mobile = models.CharField(
        help_text=_('Mobile'), max_length=32, 
        default='', blank=True, null=True)
    phone = models.CharField(
        help_text=_('Phone'), max_length=32, 
        default='', blank=True, null=True)
    address = models.CharField(
        help_text=_('Address'), max_length=512, 
        default='', blank=True, null=True)
    
    def set_password(self, raw_password):
        self.password = make_password(
            raw_password, salt = self.BACKEND_SALT + self.username)

    def set_unusable_password(self):
        # Sets a value that will never be a valid hash
        self.password = make_password(
            None, salt = self.BACKEND_SALT + self.username)

