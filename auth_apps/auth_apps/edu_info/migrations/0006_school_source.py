# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-07-26 06:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edu_info', '0005_auto_20160701_0346'),
    ]

    operations = [
        migrations.AddField(
            model_name='school',
            name='source',
            field=models.PositiveSmallIntegerField(choices=[(0, 'techu'), (1, 'user')], default=0, verbose_name='School Source'),
        ),
    ]
