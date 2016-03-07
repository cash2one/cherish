from django.contrib import admin
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.utils.translation import ugettext_lazy as _
from django.db.models.fields import Field

from auth_user.models import TechUUser 


class TechUUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = TechUUser


class TechUUserAdmin(UserAdmin):
    form = TechUUserChangeForm

    fieldsets = UserAdmin.fieldsets + (
        (_('Profile Info'), {
            'fields': ('birth_date', 'qq', 'remark', 'mobile', 'phone', 'address')
        }),
    )


admin.site.register(TechUUser, TechUUserAdmin)
