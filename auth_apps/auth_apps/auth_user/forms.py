import re
import logging
from django import forms
from django.template import loader
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from django.core.validators import validate_email
from django.core.mail import EmailMultiAlternatives
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm

from .models import TechUUser
from .tokens import mobile_token_generator

logger = logging.getLogger(__name__)


def validate_mobile(value):
    """ Raise a ValidationError if the value looks like a mobile telephone number.
    """
    rule = re.compile(r'^[0-9]{10,14}$')

    if not rule.search(value):
        msg = u"Invalid mobile number."
        raise ValidationError(msg)


class UserRegisterForm(UserCreationForm):
    error_messages = {
        'email_exist': _('The email already exist in system.'),
        'username_exist': _('Username existed, try another name please.'),
        'mobile_exist': _('Mobile number existed, try another one please.'),
        'need_reset_password_entry': _(
            'We need a reset password entry,'
            'please set email or mobile for password reset'
        ),
    }
    is_email = False
    is_mobile = False

    birth_date = forms.DateField(
        required=False, widget=forms.SelectDateWidget()
    )

    class Meta:
        model = TechUUser
        fields = [
            'username', 'email', 'mobile', 'birth_date', 'qq',
            'phone', 'address', 'remark',
        ]

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if username and TechUUser.objects.filter(username=username).exists():
            raise forms.ValidationError(
                self.error_messages['username_exist'],
                code='username_exist',
            )
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and TechUUser.objects.filter(email=email).exists():
            raise forms.ValidationError(
                self.error_messages['email_exist'],
                code='email_exist',
            )
        return email

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')
        if mobile and TechUUser.objects.filter(mobile=mobile).exists():
            raise forms.ValidationError(
                self.error_messages['mobile_exist'],
                code='mobile_exist',
            )
        return mobile

    def clean(self):
        cleaned_data = super(UserRegisterForm, self).clean()
        # required either email or mobile
        if not (cleaned_data.get('email') or cleaned_data.get('mobile')):
            raise forms.ValidationError(
                self.error_messages['need_reset_password_entry'],
                code='need_reset_password_entry',
            )
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    # set username and password to read-only
    username = forms.CharField(disabled=True)
    email = forms.EmailField(disabled=True)
    # set birth_date date selector
    birth_date = forms.DateField(
        required=False, widget=forms.SelectDateWidget()
    )

    class Meta:
        model = TechUUser
        fields = [
            'username', 'email', 'mobile', 'birth_date', 'qq',
            'phone', 'address', 'remark',
        ]


class PasswordResetForm(forms.Form):
    entry = forms.CharField(
        label=_('Entry'),
        help_text=_('Email/Mobile'),
        max_length=254,
        widget=forms.TextInput(attrs={'placeholder': _('Email/Mobile')}))

    def __init__(self, *args, **kwargs):
        super(PasswordResetForm, self).__init__(*args, **kwargs)
        self.post_reset_redirect = None

    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email,
                  html_email_template_name=None):
        """
        Sends a django.core.mail.EmailMultiAlternatives to `to_email`.
        """
        subject = loader.render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)

        email_message = EmailMultiAlternatives(
            subject, body, from_email, [to_email])
        if html_email_template_name is not None:
            html_email = loader.render_to_string(
                html_email_template_name, context)
            email_message.attach_alternative(html_email, 'text/html')

        email_message.send()

    def send_mobile(self, mobile_template_name, context, to_mobile):
        body = loader.render_to_string(mobile_template_name, context)
        # TODO: send sms message to mobile
        logger.debug('send sms : {body}'.format(body=body))

    def get_users_by_email(self, email):
        """Given an email, return matching user(s) who should receive a reset.

        This allows subclasses to more easily customize the default policies
        that prevent inactive users and users with unusable passwords from
        resetting their password.

        """
        active_users = get_user_model()._default_manager.filter(
            email__iexact=email, is_active=True)
        return (u for u in active_users if u.has_usable_password())

    def get_users_by_mobile(self, mobile):
        active_users = get_user_model()._default_manager.filter(
            mobile__iexact=mobile, is_active=True)
        return (u for u in active_users if u.has_usable_password())

    def save_email(
            self, domain_override=None,
            subject_template_name='accounts/email/password_reset_subject.txt',
            email_template_name='accounts/email/password_reset_email.html',
            use_https=False, token_generator=default_token_generator,
            from_email=None, request=None, html_email_template_name=None):
        """
        Generates a one-use only link for resetting password and sends to the
        user.
        """
        email = self.cleaned_data["entry"]
        for user in self.get_users_by_email(email):
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
            self.send_mail(subject_template_name, email_template_name,
                           context, from_email, user.email,
                           html_email_template_name=html_email_template_name)

    def save_mobile(
            self, domain_override=None,
            mobile_template_name='accounts/mobile/password_reset_mobile.html',
            token_generator=mobile_token_generator,
            use_https=False, request=None):
        """
        Generates a one-use code for resetting password and sends to the
        user.
        """
        mobile = self.cleaned_data["entry"]
        for user in self.get_users_by_mobile(mobile):
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
                kwargs = {
                    'uidb64': urlsafe_base64_encode(force_bytes(user.pk))
                }
            )
            self.send_mobile(mobile_template_name, context, user.mobile)

    def clean_entry(self):
        self.is_email = False
        self.is_mobile = False
        entry = self.cleaned_data.get('entry')
        # check input : mobile or email ?
        try:
            validate_email(entry)
            # email
            self.is_email = True
            logger.debug('clean entry: get email')
        except ValidationError:
            self.is_email = False
        if not self.is_email:
            try:
                validate_mobile(entry)
                # mobile
                self.is_mobile = True
                logger.debug('clean entry: get mobile')
            except ValidationError:
                self.is_mobile = False
        if not (self.is_email or self.is_mobile):
            raise forms.ValidationError(_('Please input email or mobile.'))
        # check entry validate in system
        if self.is_email:
            try:
                self.get_users_by_email(entry).next()
            except StopIteration:
                raise forms.ValidationError(_('Invalid email'))
        if self.is_mobile:
            try:
                self.get_users_by_mobile(entry).next()
            except StopIteration:
                raise forms.ValidationError(_('Invalid mobile nuber'))
        return entry

    def save(self, **opts):
        if self.is_email:
            self.save_email(**opts)
        elif self.is_mobile:
            self.save_mobile(**opts)
        if not self.post_reset_redirect:
            # we cannot find the right entry
            logger.error('password reset error')


class ValidCodeSetPasswordForm(SetPasswordForm):
    code = forms.RegexField(
        label=_('Code'),
        help_text=_('mobile verify code'),
        regex=r'^[0-9]+$', strip=True,
        required=True,
        max_length=mobile_token_generator.DEFAULT_CODE_LENGTH,
        widget=forms.TextInput(attrs={'placeholder': _('Code')}))
