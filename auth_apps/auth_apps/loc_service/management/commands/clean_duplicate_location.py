# -*- coding: utf-8 -*-

from collections import defaultdict

from django.db import connection
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def dictfetchall(self, cursor):
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row)) for row in cursor.fetchall()
        ]

    def handle(self, *args, **options):
        sql = "select code, name, parent_id as p_code from loc_service_location"
        name_codes = defaultdict(list)
        with connection.cursor() as c:
            c.execute(sql)

            for item in self.dictfetchall(c):
                code = item.get('code')
                name_unicode = item.get('name')
                p_code = item.get('p_code')
                name_utf8 = name_unicode.encode('utf8')
                _name = ''.join(name_unicode.split())

                if len(name_utf8) != len(_name) and len(name_utf8) / len(_name) != 3:
                    self.stderr.write(u'illegal location: {c} {n}'.format(c=code, n=name_unicode))
                    sql = 'update loc_service_location set name={n} where code={c}'.format(c=code, n=_name)
                    c.execute(sql)

                name_pcode = (_name, p_code)
                name_codes[name_pcode].append(code)

            duplicate_codes_list = filter(lambda x: len(x) > 1, name_codes.values())

            for codes in duplicate_codes_list:
                assert len(codes) == 2
                code, _code = codes
                sql = 'update edu_info_school set area_code_id={c} where area_code_id={_c}'.format(c=code, _c=_code)
                c.execute(sql)
                sql = 'delete from loc_service_location where code={c}'.format(c=_code)
                c.execute(sql)
