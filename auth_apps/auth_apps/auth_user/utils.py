import logging

from django.template import loader
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from sendsms.message import SmsMessage

logger = logging.getLogger(__name__)


def sync_send_email(
        to_email, context, from_email,
        subject_template_name, email_template_name,
        html_email_template_name=None):
    """
        Sends a django.core.mail.EmailMultiAlternatives to `to_email`.
    """
    subject = loader.render_to_string(subject_template_name, context)
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())
    body = loader.render_to_string(email_template_name, context)

    email_message = EmailMultiAlternatives(
        subject, body, from_email, [to_email])
    if html_email_template_name is not None:
        html_email = loader.render_to_string(
            html_email_template_name, context)
        email_message.attach_alternative(html_email, 'text/html')

    email_message.send()


def sync_send_mobile(to_mobile, context, mobile_template_name):
    content = loader.render_to_string(mobile_template_name, context)
    # send sms message to mobile
    body = {
        'content': content,
        'code': context.get('token'),
    }
    message = SmsMessage(body=body, to=[to_mobile])
    message.send()
    logger.debug('send sms : {body}'.format(body=body))


def get_users_by_mobile(mobile):
    active_users = get_user_model()._default_manager.filter(
        mobile__iexact=mobile, is_active=True)
    return (u for u in active_users if u.has_usable_password())


def get_users_by_email(email):
    active_users = get_user_model()._default_manager.filter(
        email__iexact=email, is_active=True)
    return (u for u in active_users if u.has_usable_password())


def get_user_by_mobile(mobile):
    user = None
    users = get_users_by_mobile(mobile)
    try:
        user = users.next()
    except StopIteration:
        return None
    return user


def get_user_by_email(email):
    user = None
    users = get_users_by_email(email)
    try:
        user = users.next()
    except StopIteration:
        return None
    return user


def check_mobile(mobile):
    return get_user_model()._default_manager.filter(
        mobile__iexact=mobile, is_active=True).exists()


def check_email(email):
    return get_user_model()._default_manager.filter(
        email__iexact=email, is_active=True).exists()
