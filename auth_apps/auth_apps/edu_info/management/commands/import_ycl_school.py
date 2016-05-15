# coding: utf-8
from django.db import connection
from django.db.utils import IntegrityError
from django.core.management.base import BaseCommand, CommandError

from loc_service.models import Location
from edu_info.models import School


class Command(BaseCommand):

    def dictfetchall(self, cursor):
        "Return all rows from a cursor as a dict"
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    def handle(self, *args, **options):
        all_categories = dict(School.SCHOOL_CATEGORIES)
        all_categories = all_categories.keys()
        sql = 'SELECT SCHOOL_ID as id, SCHOOL_AREA_CODE as code,SCHOOL_NAME as name, SCHOOL_CATEGORY as category FROM jingyou_school'
        with connection.cursor() as c:
            c.execute(sql)
            for p in self.dictfetchall(c):
                try:
                    area = Location.objects.get(code=int(p.get('code')))
                except Location.DoesNotExist:
                    self.stderr.write('cannot found area: {p}'.format(p=p))
                    continue
                category = p.get('category')
                if category not in all_categories:
                    category = School.SCHOOL_CATEGORY.UNKNOWN
                try:
                    School.objects.create(
                        school_id=int(p.get('id')),
                        area_code=area,
                        name=p.get('name'),
                        category=category
                    )
                except IntegrityError:
                    self.stderr.write('inserted {p}'.format(p=p))
