from typing import TYPE_CHECKING

import structlog as logging
from django.forms import CharField, ModelForm, MultipleChoiceField
from django.forms.widgets import CheckboxSelectMultiple, Textarea
from django_filters import CharFilter, ChoiceFilter, FilterSet

from web.forms.mixins import ReadonlyFormMixin

from .models import Mailshot

if TYPE_CHECKING:
    from django.db import QuerySet

logger = logging.get_logger(__name__)


class MailshotFilter(FilterSet):

    id = CharFilter(field_name="id", lookup_expr="icontains", label="Reference")

    title = CharFilter(field_name="title", lookup_expr="icontains", label="Title")

    description = CharFilter(field_name="description", lookup_expr="icontains", label="Description")

    status = ChoiceFilter(
        field_name="status", lookup_expr="exact", choices=Mailshot.Statuses.choices, label="Status"
    )

    class Meta:
        model = Mailshot
        fields = []


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

        if self.user.has_perm("web.reference_data_access"):
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
        fields = []


class MailshotForm(ModelForm):

    RECIPIENT_CHOICES = (
        ("importers", "Importers and Agents"),
        ("exporters", "Exporters and Agents"),
    )

    reference = CharField(disabled=True, required=False)
    status = CharField(disabled=True, required=False)
    recipients = MultipleChoiceField(choices=RECIPIENT_CHOICES, widget=CheckboxSelectMultiple())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reference"].initial = self.instance.id

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
            "reference",
            "status",
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


class MailshotReadonlyForm(ReadonlyFormMixin, MailshotForm):
    pass


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
