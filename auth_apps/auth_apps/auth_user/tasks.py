import requests
from celery import Celery
from celery.utils.log import get_task_logger
from django.conf import settings
from oauth2_provider.models import get_application_model

from .utils import sync_send_mobile, sync_send_email
from common.xplatform_service import xplatform_service

app = Celery()
logger = get_task_logger(__name__)


@app.task(bind=True)
def send_mobile_task(self, to_mobile, context, mobile_template_name):
    try:
        sync_send_mobile(to_mobile, context, mobile_template_name)
        logger.debug('send mobile to {to}, context:{c}'.format(
            to=to_mobile, c=context))
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task(bind=True)
def send_email_task(
        self, to_email, context, from_email, subject_template_name,
        email_template_name):
    try:
        sync_send_email(
            to_email, context, from_email, subject_template_name,
            email_template_name)
        logger.debug('send email to {to}, context:{c}'.format(
            to=to_email, c=context))
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task(bind=True)
def application_notify(self, client_id, context):
    try:
        apps = get_application_model().objects.filter(client_id=client_id)
        for app in apps:
            logger.debug('send notify to app({app}):{url}, context:{c}'.format(
                app=app, url=app.default_notify_uri, c=context))
            if app.notify_url:
                requests.post(
                    app.notify_url, data=context,
                    timeout=settings.DEFAULT_REQUEST_TIMEOUT)
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task(bind=True)
def xplatform_register(self, register_entries):
    try:
        logger.debug('register user entries: {entries}'.format(
                     entries=register_entries))
        xplatform_service.backend_batch_username_register(register_entries)
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task(bind=True)
def xplatform_changepwd(self, userid, username, raw_password):
    try:
        logger.debug('change password userid: {uid}, username: {uname}'.format(
                     uid=userid, uname=username))
        xplatform_service.backend_changepwd(userid, username, raw_password)
    except Exception as exc:
        raise self.retry(exc=exc)
