"""auth_apps URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin

from auth_user.views import UserRegisterView, UserRegisterDoneView, UserProfileView, HomePageView

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^oauth/', include('oauth2_provider.urls', namespace='oauth2_provider')),

    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^accounts/register/done/$', UserRegisterDoneView.as_view(), name='register_done'),
    url(r'^accounts/register/$', UserRegisterView.as_view(), name='register'),
    url(r'^accounts/profile/$', UserProfileView.as_view(), name='profile'),

    url(r'^$', HomePageView.as_view(), name='home')
]
