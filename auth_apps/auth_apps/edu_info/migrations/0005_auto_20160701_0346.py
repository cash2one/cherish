# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-07-01 03:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edu_info', '0004_auto_20160627_0912'),
    ]

    operations = [
        migrations.AlterField(
            model_name='school',
            name='school_id',
            field=models.AutoField(primary_key=True, serialize=False, verbose_name='School ID'),
        ),
    ]