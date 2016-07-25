# -*- coding: utf-8 -*-

from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction

from loc_service.models import Location
from edu_info.models import School


class Command(BaseCommand):

    def handle(self, *args, **options):

        name_codes = defaultdict(list)

        for location in Location.objects.all():
            name = location.name
            _name = ''.join(name.split())

            if name != _name:
                self.stderr.write(u'illegal location: {c} {n}'.format(
                    c=location.code, n=location.name))
                location.name = _name
                location.save()

            name_pcode = (_name, location.parent_id)
            name_codes[name_pcode].append(location.code)

        duplicate_codes_list = filter(lambda x: len(x) > 1, name_codes.values())

        for codes in duplicate_codes_list:
            code, codes = codes[0], codes[1:]

            with transaction.atomic():
                for school in School.objects.filter(area_code_id__in=codes):
                    school.area_code_id = code
                    school.save()
                for location in Location.objects.filter(code__in=codes):
                    location.delete()
