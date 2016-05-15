from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey


class Location(MPTTModel):
    code = models.IntegerField(_('Location code'), primary_key=True)
    name = models.CharField(_('Location name'), max_length=50)
    parent = TreeForeignKey(
        'self', null=True, blank=True, related_name='children', db_index=True)

    def __unicode__(self):
        return self.name

    class MPTTMeta:
        order_insertion_by = ['code']
