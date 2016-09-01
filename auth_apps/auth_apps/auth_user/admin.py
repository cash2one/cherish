from django.contrib import admin
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.utils.translation import ugettext_lazy as _
from django.db.models.fields import Field
# from db_file_storage.form_widgets import DBAdminClearableFileInput

from auth_user.models import TechUUser
from .widgets import DBAdminImageWidget


class TechUUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = TechUUser
        widgets = {
            'avatar': DBAdminImageWidget
        }


class TechUUserAdmin(UserAdmin):
    form = TechUUserChangeForm

    fieldsets = UserAdmin.fieldsets + (
        (_('Profile Info'), {
            'fields': (
                'birth_date', 'qq', 'remark', 'mobile', 'phone', 'address',
                'avatar', 'edu_profile'
            )
        }),
    )


admin.site.register(TechUUser, TechUUserAdmin)
