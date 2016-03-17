from django.conf.urls import url, include
from django.contrib.auth import views as auth_views
from rest_framework.urlpatterns import format_suffix_patterns

from .views import (
    # api views
    UserRetrieveUpdateAPIView,
    GroupRetrieveAPIView,
    MobileCodeAPIView,
    RegisterMobileCodeAPIView,
    MobileCodeResetPasswordAPIView,
    UserRegisterAPIView,
    ChangePasswordAPIView,
    # page views
    UserRegisterView,
    UserRegisterDoneView,
    UserProfileView,
    PasswordResetView,
    MobilePasswordResetConfirm,
    MobilePasswordResetComplete,
    EmailPasswordResetComplete,
)
from .forms import LoginForm
from .tokens import email_token_generator


api_urlpatterns = [
    url(
        r'^user/register/mobile/$',
        UserRegisterAPIView.as_view(),
        name='api_user_register_mobile'
    ),
    url(
        r'^user/change_password/$',
        ChangePasswordAPIView.as_view(),
        name='api_user_change_password'
    ),
    url(
        r'^user/reset_password/mobile/$',
        MobileCodeResetPasswordAPIView.as_view(),
        name='api_user_reset_password_mobile'
    ),
    url(
        r'^user/(?P<pk>[0-9]+)/$',
        UserRetrieveUpdateAPIView.as_view(),
        name='api_user_resource'
    ),
    url(
        r'^group/(?P<pk>[0-9]+)/$',
        GroupRetrieveAPIView.as_view(),
        name='api_group_resource'
    ),
    url(
        r'^mobile_code/$',
        MobileCodeAPIView.as_view(),
        name='api_mobile_code'
    ),
    url(
        r'^register/mobile_code/$', 
        RegisterMobileCodeAPIView.as_view(),
        name='api_register_mobile_code'
    ),
]

page_urlpatterns = [
    url(
        r'^register/done/$',
        UserRegisterDoneView.as_view(),
        name='register_done'
    ),
    url(r'^register/$', UserRegisterView.as_view(), name='register'),
    url(r'^profile/$', UserProfileView.as_view(), name='profile'),
    ########################
    # about login/reset
    url(
        r'^login/$',
        auth_views.login,
        {
            'template_name': 'accounts/login.html',
            'authentication_form': LoginForm,
        },
        name='login',
    ),
    url(
        r'^logout/$',
        auth_views.logout,
        {
            'template_name': 'accounts/logged_out.html'
        },
        name='logout',
    ),
    url(
        r'^password_change/$',
        auth_views.password_change,
        {
            'template_name': 'accounts/password_change_form.html'
        },
        name='password_change',
    ),
    url(
        r'^password_change/done/$',
        auth_views.password_change_done,
        {
            'template_name': 'accounts/password_change_done.html'
        },
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
        {
            'template_name': 'accounts/email/password_reset_done.html'
        },
        name='email_password_reset_done',
    ),
    url(
        r'^email/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.password_reset_confirm,
        {
            'template_name': 'accounts/email/password_reset_confirm.html',
            'post_reset_redirect': 'email_password_reset_complete',
            'token_generator': email_token_generator,
        },
        name='email_password_reset_confirm',
    ),
    url(
        r'^email/reset/complete/$',
        EmailPasswordResetComplete.as_view(),
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

versioned_api_urlpatterns = [
    url(r'^api/v1/', include(api_urlpatterns, namespace='v1')),
]
urlpatterns = page_urlpatterns + format_suffix_patterns(versioned_api_urlpatterns, allowed=['json'])
