# coding: utf-8
from __future__ import unicode_literals

import logging

logger = logging.getLogger(__name__)


class SetRemoteAddrMiddleware(object):
    def process_request(self, request):
        try:
            request.META['REMOTE_ADDR'] = request.META['HTTP_X_REAL_IP']
        except:
            request.META['REMOTE_ADDR'] = '1.1.1.1'
        logger.debug('[SetRemoteAddrMiddleware] remote addr ({ip})'.format(
            ip=request.META['REMOTE_ADDR']))
