from __future__ import unicode_literals

from django.views.generic.base import ContextMixin
from oauth2_provider import views
from braces.views import GroupRequiredMixin

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
    pass


class RevokeTokenViewWrapper(views.RevokeTokenView):
    pass


# oauth2 application management
class ApplicationListWrapper(
        GroupRequiredMixin, AppDevTagContextMixin, views.ApplicationList):
    group_required = APP_DEV_GROUP


class ApplicationRegistrationWrapper(
        GroupRequiredMixin, AppDevTagContextMixin, views.ApplicationRegistration):
    group_required = APP_DEV_GROUP


class ApplicationDetailWrapper(
        GroupRequiredMixin, AppDevTagContextMixin, views.ApplicationDetail):
    group_required = APP_DEV_GROUP


class ApplicationDeleteWrapper(
        GroupRequiredMixin, AppDevTagContextMixin, views.ApplicationDelete):
    group_required = APP_DEV_GROUP


class ApplicationUpdateWrapper(
        GroupRequiredMixin, AppDevTagContextMixin, views.ApplicationUpdate):
    group_required = APP_DEV_GROUP
    fields = ['name', 'client_id', 'client_secret', 'client_type', 
        'authorization_grant_type', 'redirect_uris']


# oauth2 token management 
class AuthorizedTokensListViewWrapper(
        GroupRequiredMixin, AppDevTagContextMixin, views.AuthorizedTokensListView):
    group_required = APP_DEV_GROUP


class AuthorizedTokenDeleteViewWrapper(
        GroupRequiredMixin, AppDevTagContextMixin, views.AuthorizedTokenDeleteView):
    group_required = APP_DEV_GROUP

