# coding: utf-8
from __future__ import unicode_literals

from django.db import connection
from django.db.utils import IntegrityError
from django.core.management.base import BaseCommand

from common.string_utils import is_number, is_other
from loc_service.models import Location
from edu_info.models import School


class Command(BaseCommand):

    def is_all_number_and_other(self, name):
        for c in name:
            if not (is_number(c) or is_other(c)):
                return False
        return True

    def handle(self, *args, **options):
        delete_sids = []
        for s in School.objects.all():
            if self.is_all_number_and_other(s.name):
                delete_sids.append(s.school_id)
        self.stderr.write('deleting {sids}'.format(sids=delete_sids))
        School.objects.filter(school_id__in=delete_sids).delete()


