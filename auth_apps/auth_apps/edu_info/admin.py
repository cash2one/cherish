from django.contrib import admin

from .models import School

class SchoolAdmin(admin.ModelAdmin):
    search_fields = ['name', 'school_id', 'area_code']


admin.site.register(School, SchoolAdmin)
