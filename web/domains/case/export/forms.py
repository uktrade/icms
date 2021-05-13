from typing import Any

import structlog as logging
from django import forms
from django.forms import CharField, Form, ModelChoiceField, ModelForm, ValidationError
from django.utils.safestring import mark_safe
from django_select2 import forms as s2forms
from django_select2.forms import ModelSelect2Widget
from guardian.shortcuts import get_objects_for_user

from web.domains.exporter.models import Exporter
from web.domains.office.models import Office
from web.domains.user.models import User

from .models import (
    CertificateOfManufactureApplication,
    ExportApplication,
    ExportApplicationType,
)

logger = logging.get_logger(__name__)


class CreateExportApplicationForm(forms.Form):
    exporter = forms.ModelChoiceField(
        queryset=Exporter.objects.none(),
        label="Main Exporter",
        widget=ModelSelect2Widget(
            attrs={
                "data-minimum-input-length": 0,
                "data-placeholder": "-- Select Exporter",
            },
            search_fields=("name__icontains"),
        ),
    )
    exporter_office = forms.ModelChoiceField(
        queryset=Office.objects.none(),
        label="Exporter Office",
        widget=ModelSelect2Widget(
            attrs={
                "data-minimum-input-length": 0,
                "data-placeholder": "-- Select Office",
            },
            search_fields=("postcode__icontains", "address__icontains"),
            dependent_fields={"exporter": "exporter"},
        ),
        help_text="The office that this certificate will be issued to.",
    )

    def __init__(self, *args: Any, user: User, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.user = user

        # Copied from original form
        main_exporters = Exporter.objects.filter(is_active=True, main_exporter__isnull=True)
        main_exporters = get_objects_for_user(
            user, "web.is_contact_of_exporter", main_exporters, with_superuser=False
        )
        main_exporter_ids = set([exporter.pk for exporter in main_exporters])

        # Copied from original form
        active_exporters = Exporter.objects.filter(is_active=True)
        exporters = get_objects_for_user(
            user, "web.is_agent_of_exporter", active_exporters, with_superuser=False
        )
        agent_exporter_ids = set([exporter.pk for exporter in exporters])

        exporters = Exporter.objects.filter(pk__in=(main_exporter_ids | agent_exporter_ids))

        self.fields["exporter"].queryset = exporters

        self.fields["exporter_office"].queryset = Office.objects.filter(
            is_active=True, exporter__in=exporters
        )


# FIXME: Remove this when happy
class NewExportApplicationForm(ModelForm):

    application_type = ModelChoiceField(
        queryset=ExportApplicationType.objects.filter(is_active=True),
        help_text=mark_safe(
            """DIT does not issue Certificates of Free Sale for food, food
        supplements, pesticides and CE marked medical devices.<br><br>

        Certificates of Manufacture are applicable only to pesticides that are
        for export only and not on free sale on the domestic market."""
        ),
    )

    exporter = ModelChoiceField(queryset=Exporter.objects.none())

    exporter_office = ModelChoiceField(
        queryset=Office.objects.none(),
        help_text="The office that this certificate will be issued to.",
    )

    def _get_agent_exporter_ids(self, user):
        """Get ids for main exporters of the given agent. """

        active_exporters = Exporter.objects.filter(is_active=True)

        exporters = get_objects_for_user(
            user, "web.is_agent_of_exporter", active_exporters, with_superuser=False
        )

        return set([exporter.pk for exporter in exporters])

    def _update_offices(self, exporter):
        if exporter in self.fields["exporter"].queryset:
            self.fields["exporter_office"].queryset = exporter.offices.filter(is_active=True)

    def _update_exporters(self, request, application_type):
        main_exporters = Exporter.objects.filter(is_active=True, main_exporter__isnull=True)

        main_exporters = get_objects_for_user(
            request.user, "web.is_contact_of_exporter", main_exporters, with_superuser=False
        )

        main_exporter_ids = set([exporter.pk for exporter in main_exporters])
        agent_exporter_ids = self._get_agent_exporter_ids(request.user)

        exporters = Exporter.objects.filter(pk__in=(main_exporter_ids | agent_exporter_ids))

        self.fields["exporter"].queryset = exporters

    def _update_form(self, request):
        type_pk = self.data.get("application_type", None)

        if not type_pk:
            return

        app_type = ExportApplicationType.objects.get(pk=type_pk)
        self._update_exporters(request, app_type)

        exporter_pk = self.data.get("exporter", None)

        if not exporter_pk:
            return

        exporter = Exporter.objects.get(pk=exporter_pk)
        self._update_offices(exporter)

    # TODO: remove once free sale certs are supported (ICMSLST-340 or ICMSLST-330)
    def clean_application_type(self):
        appl_type = self.cleaned_data["application_type"]

        if appl_type.pk == ExportApplicationType.CERT_FREE_SALE:
            raise ValidationError("Certificates of free sale are not supported yet.")

        return appl_type

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._update_form(request)

    class Meta:
        model = ExportApplication
        fields = ["application_type", "exporter", "exporter_office"]


class PrepareCertManufactureForm(ModelForm):
    class Meta:
        model = CertificateOfManufactureApplication

        fields = [
            "contact",
            "countries",
            "is_pesticide_on_free_sale_uk",
            "is_manufacturer",
            "product_name",
            "chemical_name",
            "manufacturing_process",
        ]

        help_texts = {
            "countries": """
                A certificate will be created for each country selected. You may
                select up to 40 countries. You cannot select the same country
                twice, you must submit a new application.""",
            "manufacturing_process": "Please provide an outline of the process.",
        }

        labels = {
            "is_pesticide_on_free_sale_uk": "Is the pesticide on free sale in the UK?",
            "is_manufacturer": "Is the applicant company the manufacturer of the pesticide?",
        }

        widgets = {
            "countries": s2forms.Select2MultipleWidget,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["contact"].required = True
        self.fields["is_pesticide_on_free_sale_uk"].required = True
        self.fields["is_manufacturer"].required = True

        # TODO: ICMSLST-425 change contact.queryset to be just users who should be listed
        self.fields["contact"].queryset = User.objects.filter(is_active=True)

        self.fields[
            "countries"
        ].queryset = self.instance.application_type.country_group.countries.filter(is_active=True)

    def clean_is_pesticide_on_free_sale_uk(self):
        val = self.cleaned_data["is_pesticide_on_free_sale_uk"]

        if val is None:
            raise ValidationError("You must enter this item.")

        if val:
            raise ValidationError(
                mark_safe(
                    """
                    <div class="info-box info-box-danger"><div class="screen-reader-only">Warning information box,</div>

                    <p>A Certificate of Manufacture cannot be completed for a pesticide on free sale in the UK.</p>
                    <p>To process this request contact the following:</p>
                    <ul>
                      <li>Agricultural pesticides - <a href="mailto:asg@hse.gsi.gov.uk">asg@hse.gsi.gov.uk</a>
                      <li>Non-agricultural pesticides - <a href="mailto:biocidesenquiries@hse.gsi.gov.uk">biocidesenquiries@hse.gsi.gov.uk</a>
                    </ul>
                    </div>"""
                )
            )

        return val

    def clean_is_manufacturer(self):
        val = self.cleaned_data["is_manufacturer"]

        if val is None:
            raise ValidationError("You must enter this item.")

        if not val:
            raise ValidationError(
                mark_safe(
                    """
                    <div class="info-box info-box-danger"><div class="screen-reader-only">Warning information box,</div>

                    <p>A Certificate of Manufacture can only be applied for by the manufacturer of the pesticide.</p>
                    </div>"""
                )
            )

        return val


class SubmitCertManufactureForm(Form):
    confirmation = CharField()

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.request = request

    def clean(self):
        # get rid of the "this item is required" error
        self.errors.pop("confirmation", None)

        if "_edit_application" in self.request.POST:
            return

        val = self.cleaned_data.get("confirmation")

        if val != "I AGREE":
            self.add_error(
                "confirmation", ValidationError("Please agree to the declaration of truth.")
            )

    def save(self, *args, **kwargs):
        # we're not a modelform, there's nothing to save, but the view is an
        # updateview so it calls this, so just blank this out
        return None
