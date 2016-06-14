from __future__ import unicode_literals

import string
import random
import logging
from django.db import models, transaction
from django.db.models import Q
from django.core import validators
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser, UserManager
from django.contrib.auth.hashers import make_password
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from db_file_storage.model_utils import delete_file, delete_file_if_needed
from jsonfield import JSONField

from edu_info.models import School, Subject
from common.utils import enum
from .tokens import user_mobile_token_generator
from .validators import (
    validate_mobile, validate_phone, validate_username,
    username_not_digits
)

logger = logging.getLogger(__name__)


class EduProfile(models.Model):
    USER_ROLE = enum(
        UNKNOWN=0,
        SCHOOL_ADMIN=1,
        TEACHER=2,
        STUDENT=3,
        PARENT=4
    )
    USER_ROLE_TYPES = [
        (USER_ROLE.UNKNOWN, _('Unknown')),
        (USER_ROLE.SCHOOL_ADMIN, _('School Admin')),
        (USER_ROLE.TEACHER, _('Teacher')),
        (USER_ROLE.STUDENT, _('Student')),
        (USER_ROLE.PARENT, _('Parent')),
    ]

    role = models.IntegerField(
        _('Role'), choices=USER_ROLE_TYPES, default=USER_ROLE.UNKNOWN)
    school = models.ForeignKey(
        School, on_delete=models.PROTECT, related_name='+', null=True)
    subject = models.ForeignKey(
        Subject, on_delete=models.PROTECT, related_name='+', null=True)


class DatabaseFile(models.Model):
    data = models.TextField()
    filename = models.CharField(max_length=255)
    mimetype = models.CharField(max_length=32)


class TechUUserManager(UserManager):
    def create_techu_user(self, **extra_fields):
        try:
            username = extra_fields.pop('username')
        except KeyError:
            username = self.model.autogen_username()
        try:
            email = extra_fields.pop('email')
        except KeyError:
            email = None
        try:
            password = extra_fields.pop('password')
        except KeyError:
            password = None
        return self.create_user(username, email, password, **extra_fields)

    def get_or_create_techu_user(self, **extra_fields):
        user = None
        created = False
        query_fields = dict([
            (k, v) for k, v in extra_fields.items()
            if k in self.model.IDENTITY_FIELDS
        ])
        logger.debug('[get_or_create] user query: {fields}'.format(
            fields=query_fields))
        with transaction.atomic():
            try:
                user = self.get_queryset().get(**query_fields)
            except self.model.DoesNotExist:
                created = True
                user = self.create_techu_user(**extra_fields)
            except self.model.MultipleObjectsReturned:
                logger.error('cannot identify user: {fields}'.format(
                    fields=query_fields))
        return user, created

    def update_or_create_techu_user(self, **extra_fields):
        user = None
        created = False
        query_fields = dict([
            (k, v) for k, v in extra_fields.items()
            if k in self.model.IDENTITY_FIELDS
        ])
        #logger.debug('[update_or_create] user query: {fields}'.format(
        #    fields=query_fields))
        with transaction.atomic():
            try:
                # update user
                user = self.get_queryset().get(**query_fields)
                for k, v in extra_fields.items():
                    setattr(user, k, v)
                user.save()
            except self.model.DoesNotExist:
                created = True
                user = self.create_techu_user(**extra_fields)
            except self.model.MultipleObjectsReturned:
                logger.error('cannot identify user: {fields}'.format(
                    fields=query_fields))
        return user, created



class TechUUser(AbstractUser):
    AUTO_USERNAME_PREFIX = 'auto_'
    AUTO_USERNAME_LENGTH = 16
    FRONTEND_SALT = settings.TECHU_FRONTEND_SALT
    BACKEND_SALT = settings.TECHU_BACKEND_SALT
    ERROR_MESSAGES = {
        'email_exist': _('The email already exist in system.'),
        'mobile_exist': _('Mobile number existed, try another one please.'),
        'need_reset_password_entry': _(
            'We need a reset password entry,'
            'please set email or mobile for password reset'
        ),
    }
    GENDER_TYPES = [
        (0, _('Unknown')),
        (1, _('Male')),
        (2, _('Female')),
    ]
    IDENTITY_TYPE = enum(
        USERNAME=1,
        EMAIL=2,
        MOBILE=3
    )
    IDENTITY_TYPE_MAP = {
        IDENTITY_TYPE.USERNAME: 'username',
        IDENTITY_TYPE.EMAIL: 'email',
        IDENTITY_TYPE.MOBILE: 'mobile',
    }
    IDENTITY_FIELDS = IDENTITY_TYPE_MAP.values()

    nickname = models.CharField(
        _('Nickname'), max_length=64, null=True, blank=True)
    gender = models.SmallIntegerField(
        _('Gender'), default=0, choices=GENDER_TYPES)
    birth_date = models.DateField(_('Birthday'), null=True, blank=True)
    qq = models.BigIntegerField(_('QQ'), null=True, blank=True)
    remark = models.CharField(
        _('Remark'), max_length=256, null=True, blank=True)
    mobile = models.CharField(
        _('Mobile'), max_length=32,
        validators=[validate_mobile],
        null=True, blank=True)
    phone = models.CharField(
        _('Phone'), max_length=32,
        validators=[validate_phone],
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

    objects = TechUUserManager()

    def __init__(self, *args, **kwargs):
        super(TechUUser, self).__init__(*args, **kwargs)
        self._meta.get_field('username').validators = [
            validate_username,
            username_not_digits,
        ]

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
        if not self.username:
            # auto-gen username
            self.autogen_username()

    # override
    def save(self, *args, **kwargs):
        delete_file_if_needed(self, 'avatar')
        super(TechUUser, self).save(*args, **kwargs)

    # override
    def delete(self, *args, **kwargs):
        super(TechUUser, self).delete(*args, **kwargs)
        delete_file(self, 'avatar')

    @classmethod
    def autogen_username(cls):
        # TODO: need some policy here?
        length = cls.AUTO_USERNAME_LENGTH
        return cls.AUTO_USERNAME_PREFIX + ''.join(
            random.choice(string.lowercase + string.digits)
            for i in range(length-1)
        )

    @classmethod
    def identity_type(cls, identity):
        """
            Get identity type by validation
        """
        try:
            validators.validate_email(identity)
            return cls.IDENTITY_TYPE.EMAIL
        except ValidationError:
            pass
        try:
            validate_mobile(identity)
            return cls.IDENTITY_TYPE.MOBILE
        except ValidationError:
            pass
        try:
            validate_username(identity)
            username_not_digits(identity)
            return cls.IDENTITY_TYPE.USERNAME
        except ValidationError:
            pass
        return None

    @classmethod
    def get_identity_field(cls, identity):
        """
            Get field name by identity type
        """
        itype = cls.identity_type(identity)
        return cls.IDENTITY_TYPE_MAP.get(itype)
