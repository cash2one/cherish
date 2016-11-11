from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from common.utils import enum
from loc_service.models import Location


class School(models.Model):
    SCHOOL_CATEGORY = enum(
        UNKNOWN=0,
        PRIMARY=1,
        MIDDLE=2,
        HIGH=3,
        UNIVERSITY=4,
    )
    SCHOOL_CATEGORIES = [
        (SCHOOL_CATEGORY.UNKNOWN, _('unknown')),
        (SCHOOL_CATEGORY.PRIMARY, _('primary school')),
        (SCHOOL_CATEGORY.MIDDLE, _('middle school')),
        (SCHOOL_CATEGORY.HIGH, _('high school')),
        (SCHOOL_CATEGORY.UNIVERSITY, _('university')),
    ]

    school_id = models.IntegerField(_('School ID'), primary_key=True)
    name = models.CharField(_('School Name'), max_length=255)
    pinyin = models.CharField(_('Scool PinYin'), max_length=255, default='')
    area_code = models.ForeignKey(Location, related_name='schools')
    category = models.IntegerField(
        _('School Category'),
        choices=SCHOOL_CATEGORIES,
        default=SCHOOL_CATEGORY.UNKNOWN)

    def __unicode__(self):
        return '{name}'.format(name=self.name)

    class Meta:
        ordering = ['name']


class Subject(models.Model):
    subject_id = models.IntegerField(_('Subject ID'))
    name = models.CharField(_('Subject Name'), max_length=32)

    def __unicode__(self):
        return '{name}'.format(name=self.name)
