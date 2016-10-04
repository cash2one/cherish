# coding: utf-8
import json
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
from rest_framework import status
from oauth2_provider.ext.rest_framework import TokenHasScope
from braces.views import LoginRequiredMixin

from common.xplatform_service import xplatform_service
from common.utils import enum
from .models import TechUUser
from .forms import (
    UserProfileForm, UserRegisterForm, PasswordResetForm,
    MobileCodeSetPasswordForm
)
from .serializers import (
    TechUUserSerializer, GroupSerializer, TechUMobileUserRegisterSerializer,
    TechUBackendUserRegisterSerializer
)
from .permissions import (
    IsTokenOwnerPermission, OnceUserMobileCodeCheck,
    OnceGeneralMobileCodeCheck, IPRestriction
)
from .tokens import user_mobile_token_generator, general_mobile_token_generator
from .utils import get_user_by_mobile
from .exceptions import ParameterError, OperationError
from .tasks import send_mobile_task
from .validators import validate_mobile
from .throttle import BackendAPIThrottle
from .mixins import TechUUserUpdateMixin

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
class UserRetrieveUpdateAPIView(
        generics.RetrieveUpdateAPIView, TechUUserUpdateMixin):
    """
        Get and update user info
    """
    permission_classes = [
        permissions.IsAuthenticated, TokenHasScope, IsTokenOwnerPermission
    ]
    required_scopes = ['user']
    queryset = TechUUser.objects.all()
    serializer_class = TechUUserSerializer

    # override
    # NOTICE : only support partial update
    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except:
            raise ParameterError(_('user identity not found.'))
        serializer = self.get_serializer(
            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.techu_update(user=instance, data=request.data)
        try:
            self.perform_update(serializer)
        except ValidationError as e:
            raise ParameterError(e.message)
        return Response(serializer.data)


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


class ResetPasswordBackendAPIView(APIView):
    """
        reset password from backend service
        NOTICE : use `hashed_password` to update password
        NOTE: 老客户端可能无法获得用户原始密码，因此使用hash之后的密码进行更新，
              在更新密码之后并没有向xplatform同步修改（因为不知道明文密码），
              这样导致用户在更新密码之后使用新/旧密码都可以登陆的情况：
              1. 使用新密码登陆，在xplatform验证失败，但是在本平台可以验证通过
              2. 使用老密码登陆，在xplatform验证通过
    """
    permission_classes = [
        IPRestriction,
    ]
    throttle_classes = [
        BackendAPIThrottle,
    ]

    def post(self, request, *args, **kwargs):
        identity = request.data.get('identity')
        hashed_password = request.data.get('hashed_password')
        if not (hashed_password and identity):
            raise ParameterError(
                _('need user `identity` (username, email'
                  ' or mobile) and `hashed_password`.')
            )
        # get user
        UserModel = get_user_model()
        try:
            user = UserModel._default_manager.get(**{
                UserModel.get_identity_field(identity): identity
            })
        except UserModel.DoesNotExist:
            raise ParameterError(_('user identity not found.'))
        user.update_hashed_password(hashed_password)
        user.save()
        response = {}
        return Response(response)


class UserDestroyBackendAPIView(APIView):
    """
        destroy user from backend service
        NOTE: 删除只针对本平台用户数据，并不会删除xplatform用户，
              之后的xplatform用户登陆会视同新同步用户处理
    """
    permission_classes = [
        IPRestriction,
    ]
    throttle_classes = [
        BackendAPIThrottle,
    ]

    def post(self, request, *args, **kwargs):
        users = []
        destroyed = []
        UserModel = get_user_model()
        usernames = request.data.get('usernames')
        for username in set(usernames):
            try:
                user = UserModel._default_manager.get(username=username)
            except UserModel.DoesNotExist:
                user = None
            if user:
                users.append(user)
        for user in users:
            destroyed.append(user.username)
            user.delete()
        response = {
            'destroyed': destroyed
        }
        return Response(response, status=status.HTTP_200_OK)


class UserUpdateBackendAPIView(generics.UpdateAPIView, TechUUserUpdateMixin):
    """
        update user info from backend service
        NOTE: 修改属性分为两种：
              1. 用户标识信息：用户名，手机号（如果是来自xplatform的用户，需要到xplatform更新）
              2. 其他用户属性修改

    """
    permission_classes = [
        IPRestriction,
    ]
    throttle_classes = [
        BackendAPIThrottle,
    ]
    queryset = TechUUser.objects.all()
    serializer_class = TechUUserSerializer

    # override
    # NOTICE : only support partial update
    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except:
            raise ParameterError(_('user identity not found.'))
        serializer = self.get_serializer(
            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.techu_update(user=instance, data=request.data)
        try:
            self.perform_update(serializer)
        except ValidationError as e:
            raise ParameterError(e.message)
        return Response(serializer.data)


class UserRetrieveBackendAPIView(generics.RetrieveAPIView):
    """
        get user info by user identity (username, mobile or email) from backend service
    """
    permission_classes = [
        IPRestriction,
    ]
    throttle_classes = [
        BackendAPIThrottle,
    ]
    queryset = TechUUser.objects.all()
    serializer_class = TechUUserSerializer

    # override
    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        identity = self.kwargs.get('identity')
        identity_field = TechUUser.get_identity_field(identity)
        filter_kwargs = {identity_field: identity}
        obj = get_object_or_404(queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj


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
            raise ParameterError(_('mobile already exist'))
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

    # override CreateModelMixin
    def create(self, request, *args, **kwargs):
        try:
            response = super(UserRegisterAPIView, self).create(
                request, *args, **kwargs)
        except ValidationError as e:
            raise ParameterError(e)
        return response


class UserRegisterBackendAPIView(generics.CreateAPIView):
    """
        Register new user by backend api
    """
    permission_classes = [
        IPRestriction,
    ]
    throttle_classes = [
        BackendAPIThrottle,
    ]
    queryset = TechUUser.objects.all()
    serializer_class = TechUBackendUserRegisterSerializer

    # override CreateModelMixin
    def create(self, request, *args, **kwargs):
        try:
            response = super(UserRegisterBackendAPIView, self).create(
                request, *args, **kwargs)
        except ValidationError as e:
            raise ParameterError(e)
        return response


class XPlatformNotifyAPIView(APIView):
    """
        Receive xplatform notify
    """
    def post(self, request, *args, **kwargs):
        data = json.dumps(request.data)
        code = xplatform_service.push_notify(data, self.process_handler)
        response = {
            'code': code,
        }
        return Response(response)

    @staticmethod
    def process_handler(userid, op_type):
        OP_TYPE = enum(
            CHANGE_PASSWORD=1,
            ADD_USER=2,
            DELETE_USER=3,
            EDIT_USER=4
        )
        user_info = xplatform_service.account_info(userid=userid)
        if not user_info:
            logger.warning('[Notify] not found user info. userid: {userid}'.format(
                userid=userid
            ))
            return 0
        UserModel = get_user_model()
        identity = user_info.get(u'accountName') or user_info.get(u'mobilePhone')
        try:
            user = UserModel._default_manager.get(**{
                UserModel.get_identity_field(identity): identity
            })
        except UserModel.DoesNotExist:
            user = None

        if op_type == OP_TYPE.CHANGE_PASSWORD:
            if user:
                # TODO delete user ?
                pass
        else:
            logger.warning('[Notify] received identity:{i}, op_type:{op}'.format(
                i=identity, op=op_type
            ))
        return 1
