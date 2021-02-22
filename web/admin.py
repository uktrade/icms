from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission

from web.domains.case._import.firearms.models import VerifiedCertificate
from web.domains.case._import.models import ImportApplication, ImportApplicationType
from web.domains.case.export.models import ExportApplication, ExportApplicationType
from web.domains.country.models import Country, CountryGroup
from web.flow.models import Process, Task

from .models import (
    Commodity,
    CommodityGroup,
    CommodityType,
    Importer,
    PersonalEmail,
    PhoneNumber,
    Template,
    User,
)


class CountryGroupModelForm(forms.ModelForm):
    comments = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = CountryGroup
        fields = ["name", "comments", "countries"]


class CountryGroupAdmin(admin.ModelAdmin):
    form = CountryGroupModelForm


admin.site.register(User, UserAdmin)
admin.site.register(CommodityType)
admin.site.register(Commodity)
admin.site.register(CommodityGroup)
admin.site.register(Template)
admin.site.register(Task)
admin.site.register(Process)
admin.site.register(PhoneNumber)
admin.site.register(PersonalEmail)
admin.site.register(Importer)
admin.site.register(ImportApplicationType)
admin.site.register(ExportApplicationType)
admin.site.register(CountryGroup, CountryGroupAdmin)
admin.site.register(Country)
admin.site.register(ImportApplication)
admin.site.register(VerifiedCertificate)
admin.site.register(ExportApplication)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related("content_type")
