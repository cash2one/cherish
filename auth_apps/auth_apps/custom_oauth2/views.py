from __future__ import unicode_literals

import time
import logging
try:
    import simplejson as json
except ImportError:
    import json
from django.http import HttpResponse
from django.views.generic.base import ContextMixin
from django.forms.models import modelform_factory
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.decorators.debug import sensitive_post_parameters
from oauth2_provider import views
from oauth2_provider.models import get_application_model, AccessToken
from braces.views import GroupRequiredMixin

from auth_user.backend import LoginPolicy
from custom_oauth2.oauth2_token_generator import techu_token_generator
from custom_oauth2.oauth2_token_generator import techu_refresh_token_generator

logger = logging.getLogger(__name__)

APP_DEV_GROUP = 'app_dev'


class AppDevTagContextMixin(ContextMixin):
    def get_context_data(self, **kwargs):
        context = super(AppDevTagContextMixin, self).get_context_data(**kwargs)
        context[APP_DEV_GROUP] = True
        return context


class ErrorMsgTranslationMixin(object):
    REPLACE_KEY = 'error_description'
    ERROR_MESSAGES = {
        'Invalid credentials given.': _('Invalid credentials give.'),
    }

    def do_translate(self, jbody):
        try:
            # add user info when get token success
            error_msg = jbody.get(self.REPLACE_KEY)
        except:
            return jbody
        if error_msg in self.ERROR_MESSAGES:
            try:
                jbody[self.REPLACE_KEY] = self.ERROR_MESSAGES[error_msg]
            except:
                logger.warning('fail to translate error message ({body})'.format(
                    body=jbody))
        return jbody


# oauth2 API
class AuthorizationViewWrapper(views.AuthorizationView):
    pass


class TokenViewWrapper(views.TokenView, ErrorMsgTranslationMixin):

    # override
    @classmethod
    def get_server(cls):
        server_class = cls.get_server_class()
        validator_class = cls.get_validator_class()
        return server_class(validator_class(), token_generator=techu_token_generator,
                            refresh_token_generator=techu_refresh_token_generator)

    def _get_xplatform_authority(self, user):
        ticket = None
        if user.context and type(user.context) == dict:
            ticket = {}
            if user.context.get('accountId'):
                ticket['accountId'] = user.context['accountId']
            if user.context.get('refreshToken'):
                ticket['refreshToken'] = user.context['refreshToken']
        return ticket

    def _add_user_info(self, request, jbody):
        access_token = None
        try:
            # add user info when get token success
            access_token = jbody.get('access_token')
        except:
            logger.exception('body error, type({t})'.format(t=type(jbody)))
        if access_token:
            try:
                token_obj = AccessToken.objects.select_related('user').get(token=access_token)
                jbody['user_id'] = token_obj.user.pk
                jbody['user_mobile'] = token_obj.user.mobile
                jbody['user_username'] = token_obj.user.username
                jbody['groups'] = [g.name for g in token_obj.user.groups.all()]
                jbody['server_timestamp'] = int(time.time())
                xplatform_ticket = self._get_xplatform_authority(token_obj.user)
                if xplatform_ticket:
                    jbody['xplatform'] = xplatform_ticket
            except AccessToken.DoesNotExist:
                logger.warning('fail to get user by access_token({t})'.format(
                    t=access_token))
        return jbody

    # override
    @method_decorator(sensitive_post_parameters('password'))
    def post(self, request, *args, **kwargs):
        try:
            url, headers, body, status = self.create_token_response(request)
            jbody = json.loads(body)
            jbody = self.do_translate(jbody)
            jbody = self._add_user_info(request, jbody)
            body = json.dumps(jbody)
        except LoginPolicy.LoginConstraintException:
            status = 401
            headers = {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-store',
                'Pragma': 'no-cache',
            }
            error_msg = {
                'error': 'login_constraint',
                'error_description': _("Too many times, You've limited to login"),
            }
            body = json.dumps(error_msg)
        response = HttpResponse(content=body, status=status)
        for k, v in headers.items():
            response[k] = v
        return response


class RevokeTokenViewWrapper(views.RevokeTokenView):
    pass


# oauth2 application management
class ApplicationListWrapper(
        GroupRequiredMixin, AppDevTagContextMixin, views.ApplicationList):
    group_required = APP_DEV_GROUP


class ApplicationRegistrationWrapper(
        GroupRequiredMixin,
        AppDevTagContextMixin,
        views.ApplicationRegistration):
    group_required = APP_DEV_GROUP

    def get_form_class(self):
        """
        Returns the form class for the application model
        """
        return modelform_factory(
            get_application_model(),
            fields=('name', 'client_id', 'client_secret', 'client_type',
                    'authorization_grant_type', 'redirect_uris', 'notify_uris')
        )


class ApplicationDetailWrapper(
        GroupRequiredMixin, AppDevTagContextMixin, views.ApplicationDetail):
    group_required = APP_DEV_GROUP
    fields = [
        'name', 'client_id', 'client_secret', 'client_type',
        'authorization_grant_type', 'redirect_uris', 'notify_uris'
    ]


class ApplicationDeleteWrapper(
        GroupRequiredMixin, AppDevTagContextMixin, views.ApplicationDelete):
    group_required = APP_DEV_GROUP


class ApplicationUpdateWrapper(
        GroupRequiredMixin, AppDevTagContextMixin, views.ApplicationUpdate):
    group_required = APP_DEV_GROUP
    fields = [
        'name', 'client_id', 'client_secret', 'client_type',
        'authorization_grant_type', 'redirect_uris', 'notify_uris'
    ]


# oauth2 token management
class AuthorizedTokensListViewWrapper(
        GroupRequiredMixin,
        AppDevTagContextMixin,
        views.AuthorizedTokensListView):
    group_required = APP_DEV_GROUP


class AuthorizedTokenDeleteViewWrapper(
        GroupRequiredMixin,
        AppDevTagContextMixin,
        views.AuthorizedTokenDeleteView):
    group_required = APP_DEV_GROUP
