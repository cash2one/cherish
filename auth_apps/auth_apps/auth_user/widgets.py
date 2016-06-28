# coding: utf-8
from __future__ import unicode_literals

from django import forms
from db_file_storage.form_widgets import db_file_widget


@db_file_widget
class DBImageInputWidget(forms.ClearableFileInput):
    template_with_initial = (
        '%(initial_text)s: <a target="_blank" href="%(initial_url)s">'
        '<img src="%(initial_url)s" style="height: 28px;" alt="%(initial)s"/></a> '
        '%(clear_template)s<br />%(input_text)s: %(input)s'
    )
