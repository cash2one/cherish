# coding: utf-8
import csv
from django.db import connection
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = """
        Dump users into csv file
    """

    def add_arguments(self, parser):
        parser.add_argument('--file', required=True, help='output file name')
        parser.add_argument('--fields', nargs='*', help='output fields of user, default: *')

    def handle(self, *args, **options):
        user_model = get_user_model()
        filename = options['file']
        if not filename.endswith('.csv'):
            filename = filename + '.csv'
        fields = options.get('fields', [])
        user_fields = [f.name for f, _ in user_model._meta.get_concrete_fields_with_model()]
        if fields and (set(fields) - set(user_fields)):
            raise CommandError('Invalid user field ({f}), should be ({uf})'.format(
                f=fields, uf=user_fields))
        
        with open(filename, 'wb') as f:
            writer = csv.writer(f)
            if not fields:
                fields = list(user_fields)
            # write header
            writer.writerow(fields)
            for user in user_model.objects.all():
                writer.writerow(tuple([unicode(getattr(user, f)).encode('utf-8') for f in fields]))
