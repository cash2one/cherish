# coding: utf-8
from django.db import connection
from django.core.management.base import BaseCommand, CommandError

from loc_service.models import Location


class Command(BaseCommand):

    def dictfetchall(self, cursor):
        "Return all rows from a cursor as a dict"
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    def import_node(self, node_type, sql):
        with connection.cursor() as c:
            c.execute(sql)
            for p in self.dictfetchall(c):
                try:
                    try:
                        parent = Location.objects.get(code=int(p.get('parent'))) if p.get('parent') else None
                    except Location.DoesNotExist:
                        self.stderr.write('[{nt}] cannot found parent: {p}'.format(nt=node_type,p=p))
                        continue
                    if not parent:
                        Location.objects.create(
                            code=int(p.get('code')),
                            name=p.get('name')
                        )
                    else:
                        Location.objects.create(
                            code=int(p.get('code')),
                            name=p.get('name'),
                            parent=parent
                        )
                except:
                    pass
                    # self.stderr.write('inserted {p}'.format(p=p))


    def handle(self, *args, **options):
        # import province
        sql = 'SELECT PROVINCE_CODE as code,PROVINCE_NAME as name FROM jingyou_province'
        self.import_node('province', sql)

        # import city
        sql = 'SELECT CITY_CODE as code,CITY_NAME as name,CITY_FATHER_CODE as parent FROM jingyou_city'
        self.import_node('city', sql)

        # import area
        sql = 'SELECT AREA_CODE as code,AREA_NAME as name,AREA_FATHER_CODE as parent FROM jingyou_area'
        self.import_node('area', sql)
