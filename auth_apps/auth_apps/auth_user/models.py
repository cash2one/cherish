from __future__ import unicode_literals

from django.db import models
from django.db.models import Q
from django.core import validators
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from db_file_storage.model_utils import delete_file, delete_file_if_needed
from jsonfield import JSONField

from edu_info.models import School, Subject
from common.utils import enum
from .tokens import user_mobile_token_generator


class EduProfile(models.Model):
    USER_ROLE = enum(
        SCHOOL_ADMIN=1,
        TEACHER=2,
        STUDENT=3,
        PARENT=4
    )
    USER_ROLE_TYPES = [
        (USER_ROLE.SCHOOL_ADMIN, _('School Admin')),
        (USER_ROLE.TEACHER, _('Teacher')),
        (USER_ROLE.STUDENT, _('Student')),
        (USER_ROLE.PARENT, _('Parent')),
    ]

    role = models.IntegerField(_('Role'), choices=USER_ROLE_TYPES)
    school = models.ForeignKey(
        School, on_delete=models.PROTECT, related_name='+')
    subject = models.ForeignKey(
        Subject, on_delete=models.PROTECT, related_name='+')


class DatabaseFile(models.Model):
    data = models.TextField()
    filename = models.CharField(max_length=255)
    mimetype = models.CharField(max_length=32)


class TechUUser(AbstractUser):
    FRONTEND_SALT = 'cloud_homework-'
    BACKEND_SALT = 'yzy-'
    ERROR_MESSAGES = {
        'email_exist': _('The email already exist in system.'),
        'mobile_exist': _('Mobile number existed, try another one please.'),
        'need_reset_password_entry': _(
            'We need a reset password entry,'
            'please set email or mobile for password reset'
        ),
    }

    birth_date = models.DateField(_('Birthday'), null=True, blank=True)
    qq = models.BigIntegerField(_('QQ'), null=True, blank=True)
    remark = models.CharField(
        _('Remark'), max_length=256, null=True, blank=True)
    mobile = models.CharField(
        _('Mobile'), max_length=32,
        validators=[
            validators.RegexValidator(r'^[\d]+$',
                                      _('Enter a valid mobile number. '
                                        'This value may contain only numbers'),
                                      'invalid'),
        ],
        null=True, blank=True)
    phone = models.CharField(
        _('Phone'), max_length=32,
        validators=[
            validators.RegexValidator(r'^[\d-]+$',
                                      _('Enter a valid phone number. '
                                        'This value may contain only numbers '
                                        'and - characters'), 'invalid'),
        ],
        null=True, blank=True)
    address = models.CharField(
        _('Address'), max_length=512, null=True, blank=True)
    avatar = models.ImageField(
        upload_to='auth_user.DatabaseFile/data/filename/mimetype',
        null=True, blank=True)
    edu_profile = models.OneToOneField(
        EduProfile, on_delete=models.CASCADE, related_name='user',
        null=True, blank=True)
    context = JSONField(null=True, blank=True)

    # override
    def set_password(self, raw_password):
        self.password = make_password(
            raw_password, salt=self.BACKEND_SALT + self.username)

    # override
    def set_unusable_password(self):
        # Sets a value that will never be a valid hash
        self.password = make_password(
            None, salt=self.BACKEND_SALT + self.username)

    # override
    def check_password(self, raw_password):
        if settings.ENABLE_MOBILE_PASSWORD_VERIFY:
            # check mobile verify code first
            if user_mobile_token_generator.check_token(self, raw_password):
                return True
        return super(TechUUser, self).check_password(raw_password)

    # override
    def clean(self):
        if self.email and TechUUser.objects.filter(
                ~Q(pk=self.pk), email=self.email).exists():
            raise ValidationError(
                self.ERROR_MESSAGES['email_exist'],
                code='email_exist',
            )
        if self.mobile and TechUUser.objects.filter(
                ~Q(pk=self.pk), mobile=self.mobile).exists():
            raise ValidationError(
                self.ERROR_MESSAGES['mobile_exist'],
                code='mobile_exist',
            )

    # override
    def save(self, *args, **kwargs):
        delete_file_if_needed(self, 'avatar')
        super(TechUUser, self).save(*args, **kwargs)

    # override
    def delete(self, *args, **kwargs):
        super(TechUUser, self).delete(*args, **kwargs)
        delete_file(self, 'avatar')
