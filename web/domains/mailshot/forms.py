from typing import TYPE_CHECKING, Any

import structlog as logging
from django.db import models
from django.forms import ModelForm, MultipleChoiceField
from django.forms.widgets import CheckboxInput, CheckboxSelectMultiple, Textarea
from django_filters import BooleanFilter, CharFilter, ChoiceFilter, FilterSet

from .models import Mailshot

if TYPE_CHECKING:
    from django.db import QuerySet

logger = logging.get_logger(__name__)


class MailshotFilter(FilterSet):
    reference = CharFilter(field_name="reference", lookup_expr="icontains", label="Reference")

    title = CharFilter(field_name="title", lookup_expr="icontains", label="Title")

    description = CharFilter(field_name="description", lookup_expr="icontains", label="Description")

    status = ChoiceFilter(
        field_name="status", lookup_expr="exact", choices=Mailshot.Statuses.choices, label="Status"
    )

    latest_version = BooleanFilter(
        label="Only show the current mailshot version",
        widget=CheckboxInput,
        method="get_latest_version",
    )

    class Meta:
        model = Mailshot
        fields: list[Any] = []

    def get_latest_version(
        self, queryset: "QuerySet[Mailshot]", name: str, value: bool
    ) -> "QuerySet[Mailshot]":
        """Custom method to get the latest versions for mailshots.

        :param name: field name.
        :param value: field value to filter or not the latest versions.
        """
        if value:
            last_versions = models.Q(reference__isnull=True) | models.Q(
                version=models.F("last_version_for_ref")
            )

            return queryset.filter(last_versions)

        else:
            return queryset


class ReceivedMailshotsFilter(FilterSet):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    id = CharFilter(field_name="id", lookup_expr="icontains", label="Reference")

    title = CharFilter(field_name="title", lookup_expr="icontains", label="Title")

    description = CharFilter(field_name="description", lookup_expr="icontains", label="Description")

    @property
    def qs(self) -> "QuerySet[Mailshot]":
        queryset = super().qs.filter(status=Mailshot.Statuses.PUBLISHED)

        if self.user.has_perm("web.ilb_admin"):
            return queryset

        importer_access = self.user.has_perm("web.importer_access")
        exporter_access = self.user.has_perm("web.exporter_access")

        if importer_access and exporter_access:
            return queryset

        elif importer_access:
            return queryset.filter(is_to_importers=True)

        elif exporter_access:
            return queryset.filter(is_to_exporters=True)

        else:
            return queryset.none()

    class Meta:
        model = Mailshot
        fields: list[Any] = []


class MailshotForm(ModelForm):
    RECIPIENT_CHOICES = (
        ("importers", "Importers and Agents"),
        ("exporters", "Exporters and Agents"),
    )

    recipients = MultipleChoiceField(choices=RECIPIENT_CHOICES, widget=CheckboxSelectMultiple())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        recipients = []
        if self.instance.is_to_importers:
            recipients.append("importers")
        if self.instance.is_to_exporters:
            recipients.append("exporters")
        self.fields["recipients"].initial = recipients

    def clean_recipients(self):
        recipients = self.cleaned_data["recipients"]
        self.instance.is_to_importers = "importers" in recipients
        self.instance.is_to_exporters = "exporters" in recipients
        return self.cleaned_data["recipients"]

    class Meta:
        model = Mailshot
        fields = [
            "title",
            "description",
            "is_email",
            "email_subject",
            "email_body",
            "recipients",
        ]
        widgets = {
            "description": Textarea({"rows": 4, "cols": 50}),
            "email_body": Textarea({"rows": 4, "cols": 50}),
        }


class MailshotRetractForm(ModelForm):
    class Meta:
        model = Mailshot
        fields = ["is_retraction_email", "retract_email_subject", "retract_email_body"]
        widgets = {
            "retract_email_body": Textarea({"rows": 4, "cols": 50}),
        }
        labels = {
            "is_retraction_email": "Send Emails",
            "retract_email_subject": "Email Subject",
            "retract_email_body": "Email Body",
        }
