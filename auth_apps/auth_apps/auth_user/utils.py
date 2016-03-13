import logging
import re

from django.template import loader
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives

from common.sms_service import sms_service

logger = logging.getLogger(__name__)


def validate_code(code):
    """
        Raise a ValidationError if the value doesn't look like a mobile code.
    """
    rule = re.compile(r'^[0-9]{6}$')
    if not (code and rule.search(code)):
        msg = u"Invalid code."
        raise ValidationError(msg)
    return True


def validate_mobile(value):
    """
        Raise a ValidationError if the value doesn't 
        look like a mobile telephone number.
    """
    rule = re.compile(r'^[0-9]{10,14}$')
    if not (value and rule.search(value)):
        msg = u"Invalid mobile number."
        raise ValidationError(msg)
    return True


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
    body = loader.render_to_string(mobile_template_name, context)
    # send sms message to mobile
    logger.debug('send sms : {body}'.format(body=body))
    sms_service.send_message([to_mobile], body, context.get('token'))


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
