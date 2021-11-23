import copy

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from web.domains.case.export.models import ExportApplicationType
from web.domains.user.models import User


class DjangoQuerysetJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        # Django's serializer encodes a query as a list (good) and a model as
        # a dict/object with fields for pk, model name, etc. (bad). This
        # version is more like a form POST request with a list of keys.
        if isinstance(o, models.Model):
            return o.pk

        if isinstance(o, models.QuerySet):
            return [self.default(instance) for instance in o]

        return super().default(o)


class CertificateApplicationTemplate(models.Model):
    class SharingStatuses(models.TextChoices):
        PRIVATE = ("private", "Private (do not share)")
        VIEW = ("view", "Share (view only)")
        EDIT = ("edit", "Share (allow edit)")

    name = models.CharField(
        verbose_name="Template Name",
        max_length=70,
        help_text=(
            "DIT does not issue Certificates of Free Sale for food, food supplements, pesticides"
            " and CE marked medical devices. Certificates of Manufacture are applicable only to"
            " pesticides that are for export only and not on free sale on the domestic market."
        ),
    )

    description = models.CharField(verbose_name="Template Description", max_length=500)

    application_type = models.CharField(
        verbose_name="Application Type", max_length=3, choices=ExportApplicationType.Types.choices
    )

    sharing = models.CharField(
        max_length=7,
        choices=SharingStatuses.choices,
        help_text=(
            "Whether or not other contacts of exporters/agents you are a contact of should"
            " be able view and create applications using this template, and if they can edit it."
        ),
    )

    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    data = models.JSONField(default=dict, encoder=DjangoQuerysetJSONEncoder)

    def form_data(self) -> dict:
        """Data to use as a Django form's data argument."""
        return copy.deepcopy(self.data)

    def user_can_view(self, user: User) -> bool:
        # A template may have sensitive information so we check if the user
        # should be allowed to view it (use it to create an application).
        return user == self.owner

    def user_can_edit(self, user: User) -> bool:
        # Whether the user can edit the template itself.
        return user == self.owner
