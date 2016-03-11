from __future__ import unicode_literals

from django.views.generic.base import ContextMixin
from oauth2_provider import views
from braces.views import GroupRequiredMixin

APP_DEV_GROUP = 'app_dev'


class AppDevTagContextMixin(ContextMixin):
    def get_context_data(self, **kwargs):
        context = super(AppDevTagContextMixin, self).get_context_data(**kwargs)
        context['app_dev'] = True 
        return context


class AuthorizationViewWrapper(
        GroupRequiredMixin, AppDevTagContextMixin, views.AuthorizationView):
    group_required = APP_DEV_GROUP


class TokenViewWrapper(
        GroupRequiredMixin, AppDevTagContextMixin, views.TokenView):
    group_required = APP_DEV_GROUP


class RevokeTokenViewWrapper(
        GroupRequiredMixin, AppDevTagContextMixin, views.RevokeTokenView):
    group_required = APP_DEV_GROUP


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


class ApplicationUpdateWrapper(
        GroupRequiredMixin, AppDevTagContextMixin, views.ApplicationUpdate):
    group_required = APP_DEV_GROUP


class AuthorizedTokensListViewWrapper(
        GroupRequiredMixin, AppDevTagContextMixin, views.AuthorizedTokensListView):
    group_required = APP_DEV_GROUP


class AuthorizedTokenDeleteViewWrapper(
        GroupRequiredMixin, AppDevTagContextMixin, views.AuthorizedTokenDeleteView):
    group_required = APP_DEV_GROUP

