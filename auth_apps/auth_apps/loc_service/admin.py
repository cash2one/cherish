from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from .models import Location


class LocationMPTTModelAdmin(MPTTModelAdmin):
    # specify pixel amount for this ModelAdmin only:
    mptt_level_indent = 20
    list_display = ('code', 'name')
    search_fields = ['name', 'code']


admin.site.register(Location, LocationMPTTModelAdmin)

