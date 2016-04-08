import logging
from django import forms
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from django.core.validators import validate_email
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from datetimewidget.widgets import DateWidget
# from db_file_storage.form_widgets import DBClearableFileInput

from .utils import (
    get_users_by_email, get_users_by_mobile,
    check_mobile, check_email,
)
from .models import TechUUser
from .tokens import user_mobile_token_generator
from .backend import LoginPolicy
from .widgets import DBAdminImageWidget
from .tasks import send_mobile_task, send_email_task
from .validators import validate_mobile

logger = logging.getLogger(__name__)


class UserRegisterForm(UserCreationForm):
    class Meta:
        model = TechUUser
        fields = [
            'username', 'email', 'mobile', 'first_name', 'last_name',
            'gender', 'avatar', 'edu_profile',
            'birth_date', 'qq', 'phone', 'address', 'remark',
        ]
        widgets = {
            'birth_date': DateWidget(
                options={
                    'locale': 'zh-cn',
                    'format': 'YYYY-MM-DD',
                    'viewMode': 'years',
                }
            ),
            'avatar': DBAdminImageWidget,
        }


class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = TechUUser
        fields = [
            'email', 'mobile', 'first_name', 'last_name',
            'gender', 'avatar', 'edu_profile',
            'birth_date', 'qq', 'phone', 'address', 'remark',
        ]
        widgets = {
            'birth_date': DateWidget(
                options={
                    'locale': 'zh-cn',
                    'format': 'YYYY-MM-DD',
                    'viewMode': 'years',
                }
            ),
            'avatar': DBAdminImageWidget,
        }


class PasswordResetForm(forms.Form):
    entry = forms.CharField(
        label=_('Entry'),
        help_text=_('Email/Mobile'),
        max_length=254,
        widget=forms.TextInput(attrs={'placeholder': _('Email/Mobile')}))

    def __init__(self, *args, **kwargs):
        super(PasswordResetForm, self).__init__(*args, **kwargs)
        self.post_reset_redirect = None

    def save_email(
            self, domain_override=None,
            use_https=False, token_generator=default_token_generator,
            from_email=None, request=None):
        """
        Generates a one-use only link for resetting password and sends to the
        user.
        """
        email = self.cleaned_data["entry"]
        for user in get_users_by_email(email):
            logger.info('{user} reset password by email'.format(user=user))
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            context = {
                'email': user.email,
                'domain': domain,
                'site_name': site_name,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': 'https' if use_https else 'http',
            }

            self.post_reset_redirect = reverse('email_password_reset_done')
            send_email_task.delay(
                user.email, context, from_email,
                subject_template_name='accounts/email/password_reset_subject.txt',
                email_template_name='accounts/email/password_reset_email.html')

    def save_mobile(
            self, domain_override=None,
            mobile_template_name='accounts/mobile/password_reset_mobile.html',
            token_generator=user_mobile_token_generator,
            use_https=False, request=None):
        """
        Generates a one-use code for resetting password and sends to the
        user.
        """
        mobile = self.cleaned_data["entry"]
        for user in get_users_by_mobile(mobile):
            logger.info('{user} reset password by mobile'.format(user=user))
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            context = {
                'mobile': user.mobile,
                'domain': domain,
                'site_name': site_name,
                'user': user,
                'token': token_generator.make_token(user),
            }

            self.post_reset_redirect = reverse(
                'mobile_password_reset_confirm',
                kwargs={
                    'uidb64': urlsafe_base64_encode(force_bytes(user.pk))
                }
            )
            send_mobile_task.delay(
                user.mobile, context, mobile_template_name)

    def clean_entry(self):
        self.is_email = False
        self.is_mobile = False
        entry = self.cleaned_data.get('entry')
        # check input : mobile or email ?
        try:
            validate_email(entry)
            # email
            self.is_email = True
        except ValidationError:
            pass
        if not self.is_email:
            try:
                validate_mobile(entry)
                # mobile
                self.is_mobile = True
            except ValidationError:
                pass
        if not (self.is_email or self.is_mobile):
            raise forms.ValidationError(_('Please input email or mobile.'))
        # check entry validate in system
        if self.is_email and (not check_email(entry)):
            raise forms.ValidationError(_('Invalid email'))
        if self.is_mobile and (not check_mobile(entry)):
            raise forms.ValidationError(_('Invalid mobile number'))
        return entry

    def save(self, **opts):
        if self.is_email:
            self.save_email(**opts)
        elif self.is_mobile:
            self.save_mobile(**opts)
        if not self.post_reset_redirect:
            # we cannot find the right entry
            logger.error('password reset error')


class MobileCodeSetPasswordForm(SetPasswordForm):
    code = forms.RegexField(
        label=_('Code'),
        help_text=_('mobile verify code'),
        regex=r'^[0-9]+$', strip=True,
        required=True,
        max_length=user_mobile_token_generator.DEFAULT_CODE_LENGTH,
        widget=forms.TextInput(attrs={'placeholder': _('Code')}))


class LoginForm(forms.Form):
    """
    identity/password logins.
    user can login with username, email or mobile number
    """
    identity = forms.CharField(
        label=_('Identity'),
        max_length=254,
        widget=forms.TextInput(
            attrs={'placeholder': _('Username/Email/Mobile')}
        ))
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={'placeholder': _('Password')}))

    error_messages = {
        'invalid_login': _("Please enter a correct identity and password. "
                           "Note that both fields may be case-sensitive."),
        'inactive': _("This account is inactive."),
        'login_constraint': _("Too many times, You've limited to login"),
    }

    def __init__(self, request=None, *args, **kwargs):
        """
        The 'request' parameter is set for custom auth use by subclasses.
        The form data comes in via the standard 'data' kwarg.
        """
        self.request = request
        self.user_cache = None
        super(LoginForm, self).__init__(*args, **kwargs)

    def clean(self):
        identity = self.cleaned_data.get('identity')
        password = self.cleaned_data.get('password')

        if identity and password:
            try:
                self.user_cache = authenticate(identity=identity,
                                               password=password)
                if self.user_cache is None:
                    raise forms.ValidationError(
                        self.error_messages['invalid_login'],
                        code='invalid_login',
                    )
                else:
                    self.confirm_login_allowed(self.user_cache)
            except LoginPolicy.LoginConstraintException:
                raise forms.ValidationError(
                    self.error_messages['login_constraint'],
                    code='login_constraint',
                )

        return self.cleaned_data

    def confirm_login_allowed(self, user):
        """
        Controls whether the given User may log in. This is a policy setting,
        independent of end-user authentication. This default behavior is to
        allow login by active users, and reject login by inactive users.

        If the given user cannot log in, this method should raise a
        ``forms.ValidationError``.

        If the given user may log in, this method should return None.
        """
        if not user.is_active:
            raise forms.ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache
