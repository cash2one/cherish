from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.utils.translation import ugettext_lazy as _
from django.conf.urls import url
from django.core.urlresolvers import reverse_lazy
from django.contrib.admin.sites import site
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.utils.safestring import mark_safe
from django.shortcuts import render_to_response
from django.template import RequestContext

from auth_user.models import TechUUser, EduProfile
from .widgets import DBImageInputWidget


class TechUUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = TechUUser
        widgets = {
            'avatar': DBImageInputWidget
        }


class XForeignKeyRawIdWidget(ForeignKeyRawIdWidget):
    # override
    def render(self, name, value, attrs=None):
        rel_to = self.rel.model
        if attrs is None:
            attrs = {}
        extra = []
        if rel_to in self.admin_site._registry:
            if "class" not in attrs:
                attrs['class'] = 'vForeignKeyRawIdAdminField'
            extra.append('<a href="%s" class="related-lookup"></a>' %
                         reverse_lazy('admin:admin_select_school_view'))
        output = [super(ForeignKeyRawIdWidget, self).render(name, value, attrs)] + extra
        if value:
            output.append(self.label_for_value(value))
        return mark_safe(''.join(output))


class EduProfileInline(admin.TabularInline):
    model = EduProfile
    fields = ('role', 'school', 'subject')
    raw_id_fields = ('school', )

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name in self.raw_id_fields:
            kwargs.pop('request', None)
            _type = db_field.rel.__class__.__name__
            if _type == 'ManyToOneRel':
                kwargs['widget'] = XForeignKeyRawIdWidget(db_field.rel, site)
            return db_field.formfield(**kwargs)
        return super(EduProfileInline, self).formfield_for_dbfield(db_field, **kwargs)


class TechUUserAdmin(UserAdmin):
    form = TechUUserChangeForm
    search_fields = ['username', 'email', 'mobile']

    fieldsets = UserAdmin.fieldsets + (
        (_('Profile Info'), {
            'fields': (
                'birth_date', 'qq', 'remark', 'mobile', 'phone', 'address',
                'avatar', 'source', 'context',  # 'edu_profile'
            )
        }),
    )

    inlines = [EduProfileInline]

    def select_school_view(self, request):
        opts = self.model._meta
        admin_site = self.admin_site
        context = {
            'admin_site': admin_site.name,
            'title': 'Select School',
            'opts': opts,
            'app_label': opts.app_label,
        }
        template = 'admin/admin_select_school.html'
        return render_to_response(
            template, context, context_instance=RequestContext(request)
        )

    # override
    def get_urls(self):
        return [
            url(
                r'^select_school/$',
                self.select_school_view,
                name='admin_select_school_view'
            )
        ] + super(TechUUserAdmin, self).get_urls()


admin.site.register(TechUUser, TechUUserAdmin)
