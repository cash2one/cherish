# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-04-20 08:37
from __future__ import unicode_literals

import auth_user.models
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_user', '0004_techuuser_gender'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='techuuser',
            managers=[
                ('objects', auth_user.models.TechUUserManager()),
            ],
        ),
        migrations.AlterField(
            model_name='techuuser',
            name='mobile',
            field=models.CharField(blank=True, max_length=32, null=True, validators=[django.core.validators.RegexValidator(b'^[\\d]{10,14}$', 'Invalid mobile number.')], verbose_name='Mobile'),
        ),
        migrations.AlterField(
            model_name='techuuser',
            name='phone',
            field=models.CharField(blank=True, max_length=32, null=True, validators=[django.core.validators.RegexValidator(b'^[\\d-]+$', 'Invalid phone number.')], verbose_name='Phone'),
        ),
    ]
