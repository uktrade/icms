from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.admin import SiteAdmin
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.urls import URLPattern, URLResolver, path
from guardian.admin import GuardedModelAdmin

from web.mail.api import is_valid_template_id
from web.models import (
    Commodity,
    CommodityGroup,
    CommodityType,
    Country,
    CountryGroup,
    DerogationsApplication,
    Email,
    EmailTemplate,
    ExportApplication,
    ExportApplicationType,
    Exporter,
    ImportApplication,
    ImportApplicationType,
    Importer,
    PhoneNumber,
    Process,
    SanctionsAndAdhocApplication,
    SanctionsAndAdhocApplicationGoods,
    Task,
    Template,
    User,
)
from web.permissions import Perms
from web.sites import CASEWORKER_SITE_NAME, EXPORTER_SITE_NAME, IMPORTER_SITE_NAME
from web.views import login_start_view


class CountryGroupModelForm(forms.ModelForm):
    comments = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = CountryGroup
        fields = ["name", "comments", "countries"]


class CountryGroupAdmin(admin.ModelAdmin):
    form = CountryGroupModelForm


class ImporterAdmin(GuardedModelAdmin):
    ...


class ExporterAdmin(GuardedModelAdmin):
    ...


class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = ["name", "gov_notify_template_id"]

    def clean_gov_notify_template_id(self) -> str:
        template_id = self.cleaned_data["gov_notify_template_id"]
        if not is_valid_template_id(template_id):
            raise ValidationError("GOV Notify template not found")
        return template_id


class EmailTemplateAdmin(admin.ModelAdmin):
    form = EmailTemplateForm
    fields = ("name", "gov_notify_template_id")
    readonly_fields = ("name",)

    ordering = ("name",)

    search_fields = ("name",)

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


class UserEmailInline(admin.TabularInline):
    model = Email


class SuperUserUserAdmin(UserAdmin):
    """UserAdmin class for default django admin site"""

    inlines = (UserEmailInline,)


class ICMSSiteForm(forms.ModelForm):
    name = forms.ChoiceField(
        label="Name",
        choices=[(f, f) for f in (CASEWORKER_SITE_NAME, EXPORTER_SITE_NAME, IMPORTER_SITE_NAME)],
        required=True,
    )

    class Meta:
        model = Site
        fields = ("domain", "name")


class ICMSSiteAdmin(SiteAdmin):
    form = ICMSSiteForm


admin.site.unregister(Site)
admin.site.register(Site, ICMSSiteAdmin)


admin.site.register(User, SuperUserUserAdmin)
admin.site.register(CommodityType)
admin.site.register(Commodity)
admin.site.register(CommodityGroup)
admin.site.register(Template)
admin.site.register(Task)
admin.site.register(ContentType)
admin.site.register(Process)
admin.site.register(PhoneNumber)
admin.site.register(Email)
admin.site.register(Importer, ImporterAdmin)
admin.site.register(ImportApplicationType)
admin.site.register(ExportApplicationType)
admin.site.register(CountryGroup, CountryGroupAdmin)
admin.site.register(Country)
admin.site.register(ImportApplication)
admin.site.register(ExportApplication)
admin.site.register(Exporter, ExporterAdmin)
admin.site.register(SanctionsAndAdhocApplication)
admin.site.register(SanctionsAndAdhocApplicationGoods)
admin.site.register(DerogationsApplication)
admin.site.register(EmailTemplate, EmailTemplateAdmin)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs: QuerySet[Permission] = super().get_queryset(request)

        qs = _filter_icms_permissions(qs)
        qs = qs.select_related("content_type").order_by("content_type__model")

        return qs


# Group already gets registered to improve performance of fetching system permissions
# Therefore unregister before adding GroupAdmin below
admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """Copied from django.contrib.auth.admin.GroupAdmin"""

    search_fields = ("name",)
    ordering = ("name",)
    filter_horizontal = ("permissions",)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == "permissions":
            qs: QuerySet[Permission] = kwargs.get("queryset", db_field.remote_field.model.objects)

            qs = _filter_icms_permissions(qs)

            # Avoid a major performance hit resolving permission names which
            # triggers a content_type load:
            kwargs["queryset"] = qs.select_related("content_type")

        return super().formfield_for_manytomany(db_field, request=request, **kwargs)


def _filter_icms_permissions(qs: QuerySet[Permission]) -> QuerySet[Permission]:
    return qs.filter(
        content_type__app_label="web",
        content_type__model__in=[
            # System-wide global permissions
            "globalpermission",
            # Models with object level permissions
            "importer",
            "exporter",
            "user",
            "emailtemplate",
            "email",
        ],
    )


#
# Django admin site for non superusers (the ILB team)
#
class ICMSAdminSite(admin.AdminSite):
    """ILB Admin admin site."""

    # Text to put at the end of each page's <title>.
    site_title = "ICMS site admin"

    # Text to put in each page's <h1>.
    site_header = "ICMS administration"

    # Text to put at the top of the admin index page.
    index_title = "Site administration"

    def has_permission(self, request):
        return (
            request.user.is_active
            and request.user.is_authenticated
            and request.user.has_perm(Perms.sys.is_icms_data_admin)
        )

    def get_urls(self):
        urls = super().get_urls()

        # Redirect unauthenticated users to the login_start_view instead of
        # the ModelBackend login used by the default Django admin site.
        # ICMS users should never use the ModelBackend login flow.
        login_index = _get_login_index(urls)
        urls[login_index] = path("login/", login_start_view, name="login")

        return urls


def _get_login_index(urls: list[URLPattern | URLResolver]) -> int:
    for index, url in enumerate(urls):
        if isinstance(url, URLPattern) and url.name == "login":
            return index

    raise ValueError("login view not in urls list")


class ICMSAdminUserAdmin(UserAdmin):
    """UserAdmin class for icms admin site"""

    fieldsets = (
        (None, {"fields": ("username",)}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "icms_v1_user",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    readonly_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
        "is_staff",
        "is_superuser",
        "icms_v1_user",
        # ICMS doesn't use user permissions
        "user_permissions",
        "last_login",
        "date_joined",
    )

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_active",
        "icms_v1_user",
    )
    list_filter = (
        "is_active",
        "groups",
        "icms_v1_user",
    )
    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
    )
    ordering = ("username",)
    filter_horizontal = ("groups",)

    inlines = (UserEmailInline,)


icms_admin_site = ICMSAdminSite(name="icms_admin")
icms_admin_site.register(User, ICMSAdminUserAdmin)
icms_admin_site.register(EmailTemplate, EmailTemplateAdmin)
