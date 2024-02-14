import copy
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from web.models import ExportApplicationType
from web.types import TypedTextChoices

if TYPE_CHECKING:
    from web.models import User


def encode_model_or_queryset(o: models.Model | models.QuerySet | Any) -> Any:
    match o:
        case models.Model():
            return o.pk
        case models.QuerySet():
            return [encode_model_or_queryset(instance) for instance in o]
        case _:
            return o


def encode_json_field_data(data: dict[str, Any]) -> dict[str, Any]:
    """Serialize Model and QuerySet instances so that they can be encoded using DjangoJSONEncoder.

    Previously this was done via a custom DjangoQuerysetJSONEncoder but didn't work
    after upgrading to Psycopg 3.
    """

    return {key: encode_model_or_queryset(value) for key, value in data.items()}


class CertificateApplicationTemplateManager(models.Manager):
    """Custom manager to preserve behaviour that relied on old custom DjangoQuerysetJSONEncoder."""

    def create(self, **kwargs):
        data = kwargs.pop("data", {})
        valid_data = encode_json_field_data(data)

        return super().create(data=valid_data, **kwargs)


class CertificateApplicationTemplate(models.Model):
    class SharingStatuses(TypedTextChoices):
        PRIVATE = ("private", "Private (do not share)")
        VIEW = ("view", "Share (view only)")
        EDIT = ("edit", "Share (allow edit)")

    # Create manager to handle legacy behaviour that relied on old custom DjangoQuerysetJSONEncoder.
    objects = CertificateApplicationTemplateManager()

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

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    data = models.JSONField(default=dict, encoder=DjangoJSONEncoder)

    def form_data(self) -> dict:
        """Data to use as a Django form's data argument."""
        return copy.deepcopy(self.data)

    def user_can_view(self, user: "User") -> bool:
        # A template may have sensitive information so we check if the user
        # should be allowed to view it (use it to create an application).
        return user == self.owner

    def user_can_edit(self, user: "User") -> bool:
        # Whether the user can edit the template itself.
        return user == self.owner

    def save(self, *args, **kwargs):
        self.data = encode_json_field_data(self.data)

        return super().save(*args, **kwargs)
