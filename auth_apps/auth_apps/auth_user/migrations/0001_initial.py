# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-05-03 07:00
from __future__ import unicode_literals

import auth_user.models
import django.contrib.postgres.fields.jsonb
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0007_alter_validators_add_error_messages'),
        ('edu_info', '0002_auto_20160425_0439'),
    ]

    operations = [
        migrations.CreateModel(
            name='TechUUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=30, unique=True, validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.')], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=30, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('nickname', models.CharField(blank=True, max_length=64, null=True, verbose_name='Nickname')),
                ('gender', models.SmallIntegerField(choices=[(0, 'Unknown'), (1, 'Male'), (2, 'Female')], default=0, verbose_name='Gender')),
                ('birth_date', models.DateField(blank=True, null=True, verbose_name='Birthday')),
                ('qq', models.BigIntegerField(blank=True, null=True, verbose_name='QQ')),
                ('remark', models.CharField(blank=True, max_length=256, null=True, verbose_name='Remark')),
                ('mobile', models.CharField(blank=True, max_length=32, null=True, validators=[django.core.validators.RegexValidator(b'^[\\d]{10,14}$', 'Invalid mobile number.')], verbose_name='Mobile')),
                ('phone', models.CharField(blank=True, max_length=32, null=True, validators=[django.core.validators.RegexValidator(b'^[\\d-]+$', 'Invalid phone number.')], verbose_name='Phone')),
                ('address', models.CharField(blank=True, max_length=512, null=True, verbose_name='Address')),
                ('avatar', models.ImageField(blank=True, null=True, upload_to='auth_user.DatabaseFile/data/filename/mimetype')),
                ('context', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('source', models.SmallIntegerField(choices=[(0, 'techu'), (1, 'xplatform'), (2, 'once_xplatform')], default=0, verbose_name='User Source')),
            ],
            options={
                'required_db_vendor': 'postgresql',
            },
            managers=[
                ('objects', auth_user.models.TechUUserManager()),
            ],
        ),
        migrations.CreateModel(
            name='DatabaseFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.TextField()),
                ('filename', models.CharField(max_length=255)),
                ('mimetype', models.CharField(max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name='EduProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.IntegerField(choices=[(0, 'Unknown'), (1, 'School Admin'), (2, 'Teacher'), (3, 'Student'), (4, 'Parent')], verbose_name='Role')),
                ('school', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='edu_info.School')),
                ('subject', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='edu_info.Subject')),
            ],
            options={
                'required_db_vendor': 'postgresql',
            },
        ),
        migrations.AddField(
            model_name='techuuser',
            name='edu_profile',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user', to='auth_user.EduProfile'),
        ),
        migrations.AddField(
            model_name='techuuser',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='techuuser',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions'),
        ),
    ]
