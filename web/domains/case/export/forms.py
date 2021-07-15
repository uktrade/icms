from typing import Any

import structlog as logging
from django import forms
from django.utils.safestring import mark_safe
from django_select2 import forms as s2forms
from django_select2.forms import ModelSelect2Widget
from guardian.shortcuts import get_objects_for_user

from web.domains.exporter.models import Exporter
from web.domains.office.models import Office
from web.domains.user.models import User

from .models import (
    CertificateOfFreeSaleApplication,
    CertificateOfManufactureApplication,
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


class PrepareCertManufactureForm(forms.ModelForm):
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
            raise forms.ValidationError("You must enter this item.")

        if val:
            raise forms.ValidationError(
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
            raise forms.ValidationError("You must enter this item.")

        if not val:
            raise forms.ValidationError(
                mark_safe(
                    """
                    <div class="info-box info-box-danger"><div class="screen-reader-only">Warning information box,</div>

                    <p>A Certificate of Manufacture can only be applied for by the manufacturer of the pesticide.</p>
                    </div>"""
                )
            )

        return val


class EditCFSForm(forms.ModelForm):
    class Meta:
        model = CertificateOfFreeSaleApplication

        fields = [
            "contact",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["contact"].required = True

        # TODO: ICMSLST-425 change contact.queryset to be just users who should be listed
        self.fields["contact"].queryset = User.objects.filter(is_active=True)
