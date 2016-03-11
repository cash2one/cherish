from django.conf.urls import url
from django.contrib.auth import views as auth_views
from rest_framework.urlpatterns import format_suffix_patterns

from .views import (
    UserRetrieveAPIView,
    GroupRetrieveAPIView,
    UserRegisterView,
    UserRegisterDoneView,
    UserProfileView,
    PasswordResetView,
    MobilePasswordResetConfirm,
    MobilePasswordResetComplete,
)

extra_urlpatterns = [
    url(r'^resource/user/(?P<pk>[0-9]+)/$', UserRetrieveAPIView.as_view()),
    url(r'^resource/group/(?P<pk>[0-9]+)/$', GroupRetrieveAPIView.as_view()),
]

urlpatterns = [
    url(
        r'^register/done/$',
        UserRegisterDoneView.as_view(),
        name='register_done'
    ),
    url(r'^register/$', UserRegisterView.as_view(), name='register'),
    url(r'^profile/$', UserProfileView.as_view(), name='profile'),
    # url(r'^',include('django.contrib.auth.urls')),
    url(
        r'^login/$',
        auth_views.login,
        {'template_name': 'accounts/login.html'},
        name='login',
    ),
    url(
        r'^logout/$',
        auth_views.logout,
        {'template_name': 'accounts/logged_out.html'},
        name='logout',
    ),
    url(
        r'^password_change/$',
        auth_views.password_change,
        {'template_name': 'accounts/password_change_form.html'},
        name='password_change',
    ),
    url(
        r'^password_change/done/$',
        auth_views.password_change_done,
        {'template_name': 'accounts/password_change_done.html'},
        name='password_change_done',
    ),
    url(
        r'^password_reset/$',
        PasswordResetView.as_view(),
        name='password_reset',
    ),
    ########################
    # email password reset
    url(
        r'^email/password_reset/done/$',
        auth_views.password_reset_done,
        {'template_name': 'accounts/email/password_reset_done.html'},
        name='email_password_reset_done',
    ),
    url(
        r'^email/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.password_reset_confirm,
        {
            'template_name': 'accounts/email/password_reset_confirm.html',
            'post_reset_redirect': 'email_password_reset_complete',
        },
        name='email_password_reset_confirm',
    ),
    url(
        r'^email/reset/complete/$',
        auth_views.password_reset_complete,
        {
            'template_name': 'accounts/email/password_reset_complete.html'
        },
        name='email_password_reset_complete',
    ),
    ########################
    # mobile password reset
    url(
        r'^mobile/reset/code/(?P<uidb64>[0-9A-Za-z_\-]+)/$',
        MobilePasswordResetConfirm.as_view(),
        name='mobile_password_reset_confirm',
    ),
    url(
        r'^mobile/reset/complete/$',
        MobilePasswordResetComplete.as_view(),
        name='mobile_password_reset_complete',
    ),

]

urlpatterns = urlpatterns + format_suffix_patterns(extra_urlpatterns)
