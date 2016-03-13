import requests
from celery import Celery
from celery.utils.log import get_task_logger
from django.conf import settings
from oauth2_provider.models import get_application_model

from .utils import sync_send_mobile, sync_send_email

app = Celery()
logger = get_task_logger(__name__)


@app.task(bind=True, max_retries=3)
def send_mobile_task(to_mobile, context, mobile_template_name):
    sync_send_mobile(to_mobile, context, mobile_template_name)


@app.task(bind=True, max_retries=3)
def send_email_task(
        to_email, context, from_email,
        subject_template_name, email_template_name,
        html_email_template_name):
    sync_send_email(
        to_email, context, from_email, subject_template_name,
        email_template_name, html_email_template_name)


@app.task(bind=True, max_retries=3)
def application_notify(client_id, context):
    apps = get_application_model().objects.filter(client_id=client_id)
    for app in apps:
        logger.debug('send notify to app({app}):{url}, context:{c}'.format(
            app=app, url=app.default_notify_uri, c=context))
        if app.notify_url:
            requests.post(
                app.notify_url, data=context,
                timeout=settings.DEFAULT_REQUEST_TIMEOUT)
