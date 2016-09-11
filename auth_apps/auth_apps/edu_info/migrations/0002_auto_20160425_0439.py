# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-04-25 04:39
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('loc_service', '0001_initial'),
        ('edu_info', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='school',
            options={'ordering': ['name']},
        ),
        migrations.AddField(
            model_name='school',
            name='area_code',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='schools', to='loc_service.Location'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='school',
            name='category',
            field=models.IntegerField(choices=[(0, 'unknown'), (1, 'primary school'), (2, 'middle school'), (3, 'high school'), (4, 'university')], default=0, verbose_name='School Category'),
        ),
        migrations.AddField(
            model_name='school',
            name='school_id',
            field=models.IntegerField(default=0, unique=True, verbose_name='School ID'),
        ),
    ]
