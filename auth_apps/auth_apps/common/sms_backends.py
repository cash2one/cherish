from sendsms.backends.base import BaseSmsBackend
from sendsms.message import SmsMessage

from .sms_service import techu_sms_service


class TechUSMSBackend(BaseSmsBackend):
    def send_messages(self, messages):
        for message in messages:
            for to in message.to:
                try:
                    # message.from_phone
                    # message.flash
                    body = message.body.get('content')
                    code = message.body.get('code')
                    techu_sms_service.send_message(
                        to_mobiles=[to],
                        body=body,
                        code=code)
                except:
                    if not self.fail_silently:
                        raise
