# -*- coding: utf-8 -*-

from itertools import chain
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = """
        Clean assigned duplicate mobile
    """

    reserved_name = {
        'p33622798': ['13973093178', '15813717928'],
        'p37119125': ['15869108263'],
        't36080915': ['13327254649'],
        't78926523': ['15737811898'],
        'p28025596': ['13755107788'],
        'p77556512': ['15226385131']
    }

    reserved_mobile = ['17791645544']

    def add_arguments(self, parser):
        parser.add_argument('--file', required=True, help='load file name')

    def handle(self, *args, **options):
        user_model = get_user_model()
        filename = options['file']
        mobile_name_dict = defaultdict(list)
        _mobile = list(chain(*self.reserved_name.values()))
        _del_mobile = []
        _remove = []

        with open(filename, 'rb') as f:
            for line in f.xreadlines():
                mobile, name = map(lambda x: x.strip(), line.split('|'))
                if mobile in self.reserved_mobile:
                    _del_mobile.append((name, mobile))
                    continue
                if mobile in _mobile:
                    if name in self.reserved_name.keys():
                        continue
                    _remove.append((name, mobile))
                else:
                    mobile_name_dict[mobile].append(name)

        for k, v in mobile_name_dict.iteritems():
            if 2 == len(v):
                v.sort()
                if v[1].startswith('s'):
                    _del_mobile.append(v[1], k)
                else:
                    _del_mobile.append(v[0], k)
            else:
                self.stderr.write('[WARNING] too many same user : {u} mobile : {m}'.format(u=v, m=k))

        for name, _ in _remove:
            user = user_model.objects.get(username=name)
            user.mobile = ''
            user.active = False
            user.save(update_fields=['active', 'mobile'])

        for name, _ in _del_mobile:
            user = user_model.objects.get(username=name)
            user.mobile = ''
            user.save(update_fields=['mobile'])
