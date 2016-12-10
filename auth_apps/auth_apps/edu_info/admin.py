from django.contrib import admin

from .models import School

class SchoolAdmin(admin.ModelAdmin):
    list_display = ('school_id', 'name')
    search_fields = ['name', 'school_id', 'area_code__code']


admin.site.register(School, SchoolAdmin)
