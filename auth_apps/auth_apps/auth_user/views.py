import logging

from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_text
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.shortcuts import resolve_url
from django.db import transaction
from django.views.generic.base import TemplateView
from django.contrib.auth.models import Group
from rest_framework import permissions, generics
from oauth2_provider.ext.rest_framework import TokenHasScope

from .models import TechUUser
from .forms import (
    UserProfileForm, UserRegisterForm, PasswordResetForm,
    ValidCodeSetPasswordForm
)
from .serializers import TechUUserSerializer, GroupSerializer
from .permissions import IsTokenOwnerPermission
from .tokens import mobile_token_generator

logger = logging.getLogger(__name__)


class HomePageView(TemplateView):
    template_name = 'home.html'


class UserRegisterView(View):
    form_class = UserRegisterForm
    template_name = 'accounts/register.html'

    @method_decorator(never_cache)
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {
            'form': form,
        })

    @method_decorator(sensitive_post_parameters())
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @method_decorator(transaction.atomic)
    def post(self, request, *args, **kwargs):
        form = self.form_class(data=request.POST)
        if form.is_valid():
            # add new user
            user = form.save()
            logger.info('[ADD USER] {user}'.format(user=user))
            return HttpResponseRedirect(reverse('register_done'))

        return render(request, self.template_name, {
            'form': form,
        })


class UserRegisterDoneView(View):
    template_name = 'accounts/register_done.html'

    @method_decorator(never_cache)
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


# general password reset entry
class PasswordResetView(View):
    form_class = PasswordResetForm
    template_name = 'accounts/password_reset_form.html'

    @method_decorator(csrf_protect)
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        context = {
            'form': form,
            'title': _('Password reset'),
        }
        return render(request, self.template_name, context)

    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        form = self.form_class(data=request.POST)
        context = {
            'form': form,
            'title': _('Password reset'),
        }
        if form.is_valid():
            opts = {
                'request': request,
                'use_https': request.is_secure(),
            }
            form.save(**opts)
            logger.debug('form url: {url}'.format(url=form.post_reset_redirect))
            return HttpResponseRedirect(form.post_reset_redirect)
        return render(request, self.template_name, context)


class MobilePasswordResetConfirm(View):
    form_class = ValidCodeSetPasswordForm
    template_name = 'accounts/mobile/password_reset_confirm.html'
    post_reset_redirect = 'mobile_password_reset_complete'
    token_generator = mobile_token_generator

    def _common(self, request, *args, **kwargs):
        uidb64 = kwargs.get('uidb64')
        message = None
        UserModel = get_user_model()
        try:
            # urlsafe_base64_decode() decodes to bytestring on Python 3
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = UserModel._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
            user = None
        if user is not None:
            validlink = True
            title = _('Enter new password')
            if request.method == 'POST':
                form = self.form_class(user, request.POST)
                if form.is_valid():
                    if self.token_generator.check_token(
                            user, form.cleaned_data['code']):
                        form.save()
                        logger.debug('verify code success')
                        return HttpResponseRedirect(
                            reverse(self.post_reset_redirect))
                    else:
                        message = _('verify code invalid')
            else:
                form = self.form_class(user)
        else:
            validlink = False
            form = None
            title = _('Password reset unsuccessful')
        context = {
            'validlink': validlink,
            'form': form,
            'title': title,
            'message': message,
        }
        return render(request, self.template_name, context)

    @method_decorator(csrf_protect)
    def get(self, request, *args, **kwargs):
        return self._common(request, *args, **kwargs)

    @method_decorator(sensitive_post_parameters())
    @method_decorator(never_cache)
    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        return self._common(request, *args, **kwargs)


class MobilePasswordResetComplete(View):
    template_name = 'accounts/mobile/password_reset_complete.html'

    def get(self, request, *args, **kwargs):
        context = {
            'title': _('Password reset complete'),
        }
        return render(request, self.template_name, context)


class UserProfileView(View):
    form_class = UserProfileForm
    template_name = 'accounts/profile.html'

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        auth_user = TechUUser.objects.get(pk=request.user.pk)
        assert(auth_user)
        form = self.form_class(instance=auth_user)
        return render(request, self.template_name, {
            'form': form,
        })

    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        auth_user = TechUUser.objects.get(pk=request.user.pk)
        assert(auth_user)
        form = self.form_class(instance=auth_user)
        message = None
        if form.is_valid():
            # add new user
            form.save()
            message = _('profile updated !')

        return render(request, self.template_name, {
            'message': message,
            'form': form,
        })


class UserRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = [
        permissions.IsAuthenticated, TokenHasScope, IsTokenOwnerPermission
    ]
    required_scopes = ['user']
    queryset = TechUUser.objects.all()
    serializer_class = TechUUserSerializer


class GroupRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = [
        permissions.IsAuthenticated, TokenHasScope, IsTokenOwnerPermission
    ]
    required_scopes = ['group']
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
