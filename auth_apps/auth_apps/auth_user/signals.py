# coding: utf-8
from __future__ import unicode_literals

import logging
from django.dispatch import Signal

from .tasks import xplatform_register, xplatform_changepwd

logger = logging.getLogger(__name__)

user_set_password_signal = Signal(providing_args=['user', 'raw_password'])


def user_set_password_handler(sender, **kwargs):
    """
    signal intercept for user set password
    """
    user = kwargs['user']
    raw_password = kwargs['raw_password']
    if user.pk:
        source, account_id = user.origin_id
        if source == user.USER_SOURCE.XPLATFORM:
            logger.debug('user change password use xplatform indentiry: {identity}'.format(
                         identity=account_id))
            xplatform_changepwd.delay(account_id, None, raw_password)
        else:
            logger.debug('user change password use username')
            xplatform_changepwd.delay(None, user.username, raw_password)
    else:
        logger.debug('register user set password')
        register_entries = [
            {
                'username': user.username,
                'password': raw_password,
                'nickname': user.nickname or user.username
            }
        ]
        xplatform_register.delay(register_entries)

user_set_password_signal.connect(user_set_password_handler)
