from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from auth_user.models import AuthUser 

# Define an inline admin descriptor for AuthUser model
# which acts a bit like a singleton
class AuthUserInline(admin.StackedInline):
    model = AuthUser
    can_delete = False
    verbose_name_plural = 'AuthUser'

# Define a new User admin
class UserAdmin(UserAdmin):
    inlines = (AuthUserInline, )

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
