from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission

from web.domains.case._import.firearms.models import VerifiedCertificate
from web.domains.case._import.models import ImportApplication, ImportApplicationType
from web.domains.case.export.models import ExportApplicationType
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
admin.site.register(CountryGroup)
admin.site.register(Country)
admin.site.register(ImportApplication)
admin.site.register(VerifiedCertificate)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related("content_type")
