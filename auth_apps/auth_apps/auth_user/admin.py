from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.utils.translation import ugettext_lazy as _

from auth_user.models import TechUUser
from .widgets import DBImageInputWidget


class TechUUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = TechUUser
        widgets = {
            'avatar': DBImageInputWidget
        }


class TechUUserAdmin(UserAdmin):
    form = TechUUserChangeForm
    search_fields = ['username', 'email', 'mobile']

    fieldsets = UserAdmin.fieldsets + (
        (_('Profile Info'), {
            'fields': (
                'birth_date', 'qq', 'remark', 'mobile', 'phone', 'address',
                'avatar',  # 'edu_profile'
            )
        }),
    )


admin.site.register(TechUUser, TechUUserAdmin)
