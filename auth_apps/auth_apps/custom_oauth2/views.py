from __future__ import unicode_literals

import logging
try:
    import simplejson as json
except ImportError:
    import json
from django.http import HttpResponse
from django.views.generic.base import ContextMixin
from django.forms.models import modelform_factory
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from oauth2_provider import views
from oauth2_provider.models import get_application_model, AccessToken
from braces.views import GroupRequiredMixin

logger = logging.getLogger(__name__)

APP_DEV_GROUP = 'app_dev'


class AppDevTagContextMixin(ContextMixin):
    def get_context_data(self, **kwargs):
        context = super(AppDevTagContextMixin, self).get_context_data(**kwargs)
        context[APP_DEV_GROUP] = True
        return context


# oauth2 API
class AuthorizationViewWrapper(views.AuthorizationView):
    pass


class TokenViewWrapper(views.TokenView):

    def _add_user_id(self, body):
        access_token = None
        try:
            jbody = json.loads(body)
            # add user info when get token success
            access_token = jbody.get('access_token')
        except:
            logger.exception('body error, type({t})'.format(t=type(body)))
        if access_token:
            try:
                token_obj = AccessToken.objects.get(token=access_token)
                jbody['user_id'] = token_obj.user.pk
                body = json.dumps(jbody, ensure_ascii=False)
            except AccessToken.DoesNotExist:
                logger.warning('fail to get user by access_token({t})'.format(
                    t=access_token))
        return body

    # override
    @method_decorator(sensitive_post_parameters('password'))
    def post(self, request, *args, **kwargs):
        url, headers, body, status = self.create_token_response(request)
        body = self._add_user_id(body)
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
