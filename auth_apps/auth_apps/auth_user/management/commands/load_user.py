# coding: utf-8

import csv
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = """
        Load users by csv file
    """

    def add_arguments(self, parser):
        parser.add_argument('--file', required=True, help='load file name')

    def handle(self, *args, **options):
        user_model = get_user_model()
        filename = options['file']

        with open(filename, 'rb') as f:
            reader = csv.reader(f)
            fields = []
            for row in reader:
                row = map(lambda x: x.strip(), row)
                if not fields:
                    fields = row
                else:
                    info = dict(zip(fields, row))
                    user, created = user_model.objects.get_or_create_techu_user(
                        **info
                    )
                    if not created:
                        self.stderr.write('[WARNING] existed user: {info}'.format(info=info))
