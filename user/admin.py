from django.apps import apps
from django.contrib import admin
from django.db.models import ManyToOneRel, ForeignKey, OneToOneField


class ListAdminMixin(object):
    def __init__(self, model, admin_site):
        self.list_display = [field.name for field in model._meta.fields]
        self.list_select_related = [x.name for x in model._meta.fields if isinstance(x, (ManyToOneRel, ForeignKey, OneToOneField,))]

        # self.search_fields=[model.p]
        super(ListAdminMixin, self).__init__(model, admin_site)


models = apps.get_models()
for model in models:
    if not str(model._meta).startswith('user'):
        continue
    admin_class = type('AdminClass', (ListAdminMixin, admin.ModelAdmin), {})
    try:
        admin.site.register(model, admin_class)
    except admin.sites.AlreadyRegistered:
        pass

admin.AdminSite.site_header = 'Recommend System Back Office'
admin.AdminSite.site_title = 'Recommend System Back Office'
