import logging

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse, reverse_lazy
from django.core.exceptions import ValidationError
from django.views.generic import View
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth import get_user_model, password_validation
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_text
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.contrib.auth.models import Group
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from rest_framework import permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from oauth2_provider.ext.rest_framework import TokenHasScope
from braces.views import LoginRequiredMixin

from .models import TechUUser
from .forms import (
    UserProfileForm, UserRegisterForm, PasswordResetForm,
    MobileCodeSetPasswordForm
)
from .serializers import (
    TechUUserSerializer, GroupSerializer, TechUMobileUserRegisterSerializer
)
from .permissions import (
    IsTokenOwnerPermission, OnceUserMobileCodeCheck, OnceGeneralMobileCodeCheck
)
from .tokens import user_mobile_token_generator, general_mobile_token_generator
from .utils import validate_mobile, get_user_by_mobile
from .exceptions import ParameterError, OperationError
from .tasks import send_mobile_task

logger = logging.getLogger(__name__)


class HomePageView(TemplateView):
    template_name = 'home.html'


##########################
# pages
class UserRegisterView(CreateView):
    model = TechUUser
    success_url = reverse_lazy('register_done')
    form_class = UserRegisterForm
    template_name = 'accounts/register.html'


class UserRegisterDoneView(TemplateView):
    template_name = 'accounts/register_done.html'


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
            return HttpResponseRedirect(form.post_reset_redirect)
        return render(request, self.template_name, context)


class MobilePasswordResetConfirm(View):
    form_class = MobileCodeSetPasswordForm
    template_name = 'accounts/mobile/password_reset_confirm.html'
    post_reset_redirect = 'mobile_password_reset_complete'
    token_generator = user_mobile_token_generator

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
            'title': _('Password reset by mobile complete'),
        }
        return render(request, self.template_name, context)


class EmailPasswordResetComplete(View):
    template_name = 'accounts/email/password_reset_complete.html'

    def get(self, request, *args, **kwargs):
        context = {
            'title': _('Password reset by email complete'),
        }
        return render(request, self.template_name, context)


class UserProfileView(LoginRequiredMixin, UpdateView):
    model = TechUUser
    success_url = reverse_lazy('profile')
    form_class = UserProfileForm
    template_name = 'accounts/profile.html'

    # override
    def get_object(self):
        return get_object_or_404(self.model, pk=self.request.user.pk)


##########################
# APIs
class UserRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    """
        Get and update user info
    """
    permission_classes = [
        permissions.IsAuthenticated, TokenHasScope, IsTokenOwnerPermission
    ]
    required_scopes = ['user']
    queryset = TechUUser.objects.all()
    serializer_class = TechUUserSerializer


class GroupRetrieveAPIView(generics.RetrieveAPIView):
    """
        Get user group info
    """
    permission_classes = [
        permissions.IsAuthenticated, TokenHasScope, IsTokenOwnerPermission
    ]
    required_scopes = ['group']
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class ChangePasswordAPIView(APIView):
    """
        change password by offering old password
    """
    permission_classes = [
        permissions.IsAuthenticated,
        TokenHasScope,
        IsTokenOwnerPermission,
    ]
    required_scopes = ['user']

    def post(self, request, *args, **kwargs):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        if not (old_password and new_password):
            raise ParameterError(_('need both new and old password'))
        user = request.user
        try:
            password_validation.validate_password(old_password, user)
            password_validation.validate_password(new_password, user)
        except:
            raise ParameterError(_('invalid password'))
        # update new password
        if not user.check_password(old_password):
            raise OperationError(_('old password error'))
        user.set_password(new_password)
        user.save()
        response = {}
        return Response(response)


class MobileCodeResetPasswordAPIView(APIView):
    """
        reset password by offering mobile code
    """
    permission_classes = [
        OnceGeneralMobileCodeCheck,
    ]

    def post(self, request, *args, **kwargs):
        mobile = request.data.get('mobile')
        new_password = request.data.get('new_password')
        if not (new_password and mobile):
            raise ParameterError(_('need new password, mobile'))
        user = get_user_by_mobile(mobile)
        if not user:
            raise ParameterError(_('mobile number not exist'))
        try:
            password_validation.validate_password(new_password, user)
        except:
            raise ParameterError(_('invalid password'))
        # update new password
        user.set_password(new_password)
        user.save()
        response = {}
        return Response(response)


class MobileCodeAPIView(APIView):
    """
        Send code by mobile, no permission constraint
        TODO: need throttle control
    """
    def post(self, request, *args, **kwargs):
        mobile = request.data.get('mobile')
        try:
            validate_mobile(mobile)
        except ValidationError:
            raise ParameterError(_('mobile number invalid'))
        user = get_user_by_mobile(mobile)
        if not user:
            raise ParameterError(_('mobile number not exist'))
        current_site = get_current_site(request)
        code = general_mobile_token_generator.make_token(mobile)
        send_mobile_task.delay(
            mobile,
            context={
                'mobile': mobile,
                'domain': current_site.domain,
                'site_name': current_site.name,
                'token': code,
                },
            mobile_template_name='accounts/mobile/verify_code.html'
            )
        response = {
            'mobile': mobile,
            'code': code,
            'countdown': settings.MOBILE_CODE_COUNTDOWN,
        }
        return Response(response)


class RegisterMobileCodeAPIView(APIView):
    """
        Send code by mobile, no permission constraint
        TODO: need throttle control
    """
    def post(self, request, *args, **kwargs):
        mobile = request.data.get('mobile')
        try:
            validate_mobile(mobile)
        except ValidationError:
            raise ParameterError(_('mobile number invalid'))
        user = get_user_by_mobile(mobile)
        if user:
            raise self.OperationError(_('mobile already exist'))
        current_site = get_current_site(request)
        code = general_mobile_token_generator.make_token(mobile)
        send_mobile_task.delay(
            mobile,
            context={
                'mobile': mobile,
                'domain': current_site.domain,
                'site_name': current_site.name,
                'token': code,
                },
            mobile_template_name='accounts/mobile/verify_code.html'
            )
        response = {
            'mobile': mobile,
            'code': code,
            'countdown': settings.MOBILE_CODE_COUNTDOWN,
        }
        return Response(response)


class UserRegisterAPIView(generics.CreateAPIView):
    """
        Register new user, need general mobile code check
    """
    permission_classes = [
        OnceGeneralMobileCodeCheck,
    ]
    queryset = TechUUser.objects.all()
    serializer_class = TechUMobileUserRegisterSerializer
