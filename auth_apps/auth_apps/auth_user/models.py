from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def new_user_added(sender, **kwargs):
    user = kwargs.get('instance')
    AuthUser.objects.get_or_create(user=user)


class AuthUser(models.Model):
    user = models.OneToOneField(User, primary_key=True)
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
