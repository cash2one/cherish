from __future__ import absolute_import
from django.conf.urls import url

from . import views

urlpatterns = (
    url(r'^authorize/$',
        views.AuthorizationViewWrapper.as_view(), name="authorize"),
    url(r'^token/$',
        views.TokenViewWrapper.as_view(), name="token"),
    url(r'^revoke_token/$',
        views.RevokeTokenViewWrapper.as_view(), name="revoke-token"),
)

# Application management views
urlpatterns += (
    url(r'^applications/$',
        views.ApplicationListWrapper.as_view(), name="list"),
    url(r'^applications/register/$',
        views.ApplicationRegistrationWrapper.as_view(), name="register"),
    url(r'^applications/(?P<pk>\d+)/$',
        views.ApplicationDetailWrapper.as_view(), name="detail"),
    url(r'^applications/(?P<pk>\d+)/delete/$',
        views.ApplicationDeleteWrapper.as_view(), name="delete"),
    url(r'^applications/(?P<pk>\d+)/update/$',
        views.ApplicationUpdateWrapper.as_view(), name="update"),
)

urlpatterns += (
    url(r'^authorized_tokens/$',
        views.AuthorizedTokensListViewWrapper.as_view(),
        name="authorized-token-list"),
    url(r'^authorized_tokens/(?P<pk>\d+)/delete/$',
        views.AuthorizedTokenDeleteViewWrapper.as_view(),
        name="authorized-token-delete"),
)
