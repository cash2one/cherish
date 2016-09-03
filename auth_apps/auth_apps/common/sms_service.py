# coding: utf-8
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class SMSService(object):
    DEFAULT_SMS_REQUEST_TIMEOUT = 3  # seconds

    def __init__(self, base_url):
        self.base_url = base_url
        self.timeout = settings.SMS_REQUEST_TIMEOUT \
            if hasattr(settings, 'SMS_REQUEST_TIMEOUT') \
            else self.DEFAULT_SMS_REQUEST_TIMEOUT

    def send_message(self, to_mobiles, body, code):
        url = self.base_url + '/code'
        payload = {
            'receivers': to_mobiles,
            'code': code,
        }
        try:
            requests.post(url, data=payload, timeout=self.timeout)
        except:
            logger.exception('[SMS SERVICE] send message error')
            return False
        logger.debug('[SMS SERVICE] send message success')
        return True


techu_sms_service = SMSService(settings.SMS_SERVICE_URL)
