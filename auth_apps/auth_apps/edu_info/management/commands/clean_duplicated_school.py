# coding: utf-8
from collections import defaultdict
from django.db import connection
from django.db.utils import IntegrityError
from django.core.management.base import BaseCommand

from loc_service.models import Location
from edu_info.models import School


class Command(BaseCommand):

    def handle(self, *args, **options):
        dup_dict = defaultdict(list)
        for s in School.objects.select_related('area_code').all():
            dup_dict[(s.area_code, s.name, s.category)].append(s)
        delete_sids = []
        for k, v in dup_dict.iteritems():
            if len(v) > 1:
                # area, name, category = k
                sids = sorted([s.school_id for s in v])
                delete_sids.extend(sids[1:])
        self.stderr.write('deleting {sids}'.format(sids=delete_sids))
        School.objects.filter(school_id__in=delete_sids).delete()


