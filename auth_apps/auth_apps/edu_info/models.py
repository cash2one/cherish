from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _


class School(models.Model):
    name = models.CharField(_('School Name'), max_length=255)


class Subject(models.Model):
    subject_id = models.IntegerField(_('Subject ID'))
    name = models.CharField(_('Subject Name'), max_length=32)
