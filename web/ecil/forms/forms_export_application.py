from typing import Any

from django.db.models import QuerySet
from guardian.shortcuts import get_objects_for_user
from markupsafe import Markup, escape

from web.ecil.gds import forms as gds_forms
from web.models import (
    CertificateOfFreeSaleApplication,
    Country,
    ECILUserExportApplication,
    ExportApplication,
    Exporter,
    Office,
    User,
)
from web.models.shared import YesNoChoices
from web.permissions import Perms


class ExportApplicationTypeForm(gds_forms.GDSModelForm):
    app_type = gds_forms.GovUKRadioInputField(
        label="Which certificate are you applying for?",
        error_messages={
            "required": "Select the certificate you are applying for.",
        },
        choices=[
            ("cfs", "Certificate of Free Sale (CFS)"),
            ("com", "Certificate of Manufacture (CoM)"),
            ("gmp", "Certificate of Good Manufacturing Practice (CGMP)"),
        ],
        choice_hints={
            "cfs": "Products which meet UK standards that fall under Department for Business and Trade regulation.",
            "com": "Pesticides that are solely for use in overseas markets and will not be placed on the UK market.",
            "gmp": "Cosmetic products which meet UK good manufacturing practice standards. For use in China only.",
        },
        choice_classes="govuk-!-font-weight-bold",
        gds_field_kwargs=gds_forms.FIELDSET_LEGEND_HEADER,
    )

    class Meta(gds_forms.GDSModelForm.Meta):
        model = ECILUserExportApplication
        fields = ["app_type"]


class ExportApplicationExporterForm(gds_forms.GDSModelForm):
    exporter = gds_forms.GovUKRadioInputField(
        label="Which company do you want an export certificate for?",
        error_messages={"required": "Select the company you want an export certificate for."},
        gds_field_kwargs=gds_forms.FIELDSET_LEGEND_HEADER,
    )

    class Meta(gds_forms.GDSModelForm.Meta):
        model = ECILUserExportApplication
        fields = ["exporter"]

    def clean_exporter(self) -> Exporter | None:
        exporter_pk = self.cleaned_data["exporter"]

        if exporter_pk == gds_forms.GovUKRadioInputField.NONE_OF_THESE:
            # None is a valid option when NONE_OF_THESE is chosen.
            self.fields["exporter"].required = False

            return None

        return self.exporters.get(pk=exporter_pk)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        # Main exporters the user can edit or is an agent of.
        self.exporters = get_user_editable_exporters(self.instance.created_by)
        self.fields["exporter"].choices = get_exporter_choices(self.exporters)


class ExportApplicationExporterOfficeForm(gds_forms.GDSModelForm):
    exporter_office = gds_forms.GovUKRadioInputField(
        label="Where will the certificate be issued to?",
        error_messages={"required": "Select the address you want an export certificate for."},
        gds_field_kwargs=gds_forms.FIELDSET_LEGEND_HEADER,
    )

    class Meta(gds_forms.GDSModelForm.Meta):
        model = ECILUserExportApplication
        fields = ["exporter_office"]

    def clean_exporter_office(self) -> Office | None:
        office_pk = self.cleaned_data["exporter_office"]

        if office_pk == gds_forms.GovUKRadioInputField.NONE_OF_THESE:
            # None is a valid option when NONE_OF_THESE is chosen.
            self.fields["exporter_office"].required = False
            return None

        return self.offices.get(pk=office_pk)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.offices = get_user_offices(self.instance.created_by, self.instance.exporter)
        self.fields["exporter_office"].choices = get_office_choices(self.offices)


class ExportApplicationNewExporterOfficeForm(gds_forms.GDSModelForm):
    class Meta(gds_forms.GDSModelForm.Meta):
        model = Office
        fields = [
            "address_1",
            "address_2",
            "address_3",
            "address_4",
            "address_5",
            "postcode",
        ]
        error_messages = {
            "address_1": {"required": "Enter address 1"},
        }

        labels = {
            "address_1": "Address line 1",
            "address_2": "Address line 2 (optional) ",
            "address_3": "Address line 3 (optional) ",
            "address_4": "Town or city (optional) ",
            "address_5": "County (optional)",
            "postcode": "Postcode (optional)",
        }

        formfield_callback = gds_forms.GDSFormfieldCallback(
            # Autocomplete link:
            # https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/autocomplete#address-line1
            gds_field_kwargs={
                "address_1": {"autocomplete": "address-line1"},
                "address_2": {"autocomplete": "address-line2"},
                "address_3": {"autocomplete": "address-line3"},
                "address_4": {
                    "autocomplete": "address-level2",
                    "classes": "govuk-!-width-two-thirds",
                },
                "address_5": {
                    "autocomplete": "address-level1",
                    "classes": "govuk-!-width-two-thirds",
                },
                "postcode": {"autocomplete": "postal-code", "classes": "govuk-input--width-10"},
            }
        )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["postcode"].required = False


class CreateExportApplicationSummaryForm(gds_forms.GDSModelForm):
    class Meta(gds_forms.GDSModelForm.Meta):
        model = ECILUserExportApplication
        fields = [
            "app_type",
            "exporter",
            "exporter_office",
        ]
        labels = {
            "app_type": "Which certificate are you applying for?",
            "exporter": "Which company do you want an export certificate for?",
            "exporter_office": "Where will the certificate be issued to?",
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        exporters = get_user_editable_exporters(self.instance.created_by)
        self.fields["exporter"].choices = get_exporter_choices(exporters)

        offices = get_user_offices(self.instance.created_by, self.instance.exporter)
        self.fields["exporter_office"].choices = get_office_choices(offices)


class ExportApplicationExporterAgentForm(gds_forms.GDSModelForm):
    agent = gds_forms.GovUKRadioInputField(
        label="Which agent company are you working for?",
        error_messages={"required": "Select the company you want an export certificate for."},
        gds_field_kwargs=gds_forms.FIELDSET_LEGEND_HEADER,
    )

    class Meta(gds_forms.GDSModelForm.Meta):
        model = ECILUserExportApplication
        fields = ["agent"]

    def clean_agent(self) -> Exporter | None:
        exporter_pk = self.cleaned_data["agent"]

        if exporter_pk == gds_forms.GovUKRadioInputField.NONE_OF_THESE:
            # None is a valid option when NONE_OF_THESE is chosen.
            self.fields["agent"].required = False

            return None

        return self.exporters.get(pk=exporter_pk)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        if self.instance.exporter:
            # Agent exporters linked to the main exporter that the user is an agent of.
            agent_exporters = get_user_agent_exporters(self.instance.created_by)
            self.exporters = agent_exporters.filter(main_exporter=self.instance.exporter)
        else:
            self.exporters = Exporter.objects.none()

        self.fields["agent"].choices = get_exporter_choices(self.exporters)


class ExportApplicationExporterAgentOfficeForm(gds_forms.GDSModelForm):
    agent_office = gds_forms.GovUKRadioInputField(
        label="What is the agent company’s office address?",
        error_messages={"required": "Select the agent company's offices address."},
        gds_field_kwargs=gds_forms.FIELDSET_LEGEND_HEADER,
    )

    class Meta(gds_forms.GDSModelForm.Meta):
        model = ECILUserExportApplication
        fields = ["agent_office"]

    def clean_agent_office(self) -> Office | None:
        office_pk = self.cleaned_data["agent_office"]

        if office_pk == gds_forms.GovUKRadioInputField.NONE_OF_THESE:
            # None is a valid option when NONE_OF_THESE is chosen.
            self.fields["agent_office"].required = False
            return None

        return self.offices.get(pk=office_pk)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        if self.instance.agent:
            # Agent exporters the user is an agent of.
            agent_exporters = get_user_agent_exporters(self.instance.created_by)
            selected_agent = agent_exporters.filter(pk=self.instance.agent.pk).first()
        else:
            selected_agent = None

        if selected_agent:
            self.offices = selected_agent.offices.filter(is_active=True)
        else:
            self.offices = Office.objects.none()

        self.fields["agent_office"].choices = get_office_choices(self.offices)


class CreateExportApplicationAgentSummaryForm(gds_forms.GDSModelForm):
    class Meta(gds_forms.GDSModelForm.Meta):
        model = ECILUserExportApplication
        fields = [
            "app_type",
            "exporter",
            "exporter_office",
            "agent",
            "agent_office",
        ]
        labels = {
            "app_type": "Which certificate are you applying for?",
            "exporter": "Which company do you want an export certificate for?",
            "exporter_office": "Where will the certificate be issued to?",
            "agent": "Which agent company are you working for?",
            "agent_office": "What is the agent company’s office address?",
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        # Set exporter choices
        exporters = get_user_editable_exporters(self.instance.created_by)
        self.fields["exporter"].choices = get_exporter_choices(exporters)

        # Set exporter_office choices
        offices = get_user_offices(self.instance.created_by, self.instance.exporter)
        self.fields["exporter_office"].choices = get_office_choices(offices)

        # Set agent choices
        if self.instance.exporter:
            # Agent exporters linked to the main exporter that the user is an agent of.
            agent_exporters = get_user_agent_exporters(self.instance.created_by).filter(
                main_exporter=self.instance.exporter
            )
        else:
            agent_exporters = Exporter.objects.none()

        self.fields["agent"].choices = get_exporter_choices(agent_exporters)

        # Set agent_office choices
        if self.instance.agent:
            # Agent exporters the user is an agent of.
            selected_agent = agent_exporters.filter(pk=self.instance.agent.pk).first()
        else:
            selected_agent = None

        if selected_agent:
            agent_offices = selected_agent.offices.filter(is_active=True)
        else:
            agent_offices = Office.objects.none()

        self.fields["agent_office"].choices = get_office_choices(agent_offices)


class ExportApplicationAddExportCountryForm(gds_forms.GDSModelForm):
    countries = gds_forms.GovUKSelectModelField(
        label="Where do you want to export products?",
        help_text=(
            "Enter a country or territory and select from the results."
            " You can add up to 40 countries or territories."
        ),
        queryset=Country.objects.none(),
        gds_field_kwargs=gds_forms.LABEL_HEADER,
        error_messages={"required": "Add a country or territory"},
    )

    class Meta(gds_forms.GDSModelForm.Meta):
        model = ExportApplication
        fields = ["countries"]

    def __init__(self, *args: Any, initial: dict[str, Any] | None = None, **kwargs: Any) -> None:
        if not initial:
            initial = {}

        # countries is a ManyToMany and sets the initial value to a list.
        # A list is not a supported value for gds_forms.GovUKSelectModelField.
        # This form is for adding legislations only so override the initial value to "".
        initial["countries"] = ""
        super().__init__(*args, initial=initial, **kwargs)
        self.selected_countries = self.instance.countries.all()

        self.fields["countries"].queryset = self.get_countries_qs()

    def clean(self) -> None:
        cleaned_data = super().clean()
        if (
            self.selected_countries
            and cleaned_data.get("countries")
            and len(self.selected_countries) >= 40
        ):
            self.add_error("countries", "You can only add up to 40 countries or territories")

        return cleaned_data

    def get_countries_qs(self) -> QuerySet[Country]:
        if isinstance(self.instance, CertificateOfFreeSaleApplication):
            return Country.app.get_cfs_countries()

        return Country.util.get_all_countries()

    def _save_m2m(self) -> None:
        """Custom method to save the new country to the set of existing countries."""
        new_country = self.cleaned_data["countries"]

        self.instance.countries.add(new_country)
        self.instance.save()


class ExportApplicationAddAnotherExportCountryForm(gds_forms.GDSForm):
    add_another = gds_forms.GovUKRadioInputField(
        label="Do you need to add another country or territory?",
        choices=YesNoChoices.choices,
        gds_field_kwargs={"fieldset": {"legend": {"classes": "govuk-fieldset__legend--m"}}},
        error_messages={"required": "Select yes or no"},
    )


class ExportApplicationRemoveExportCountryForm(gds_forms.GDSForm):
    are_you_sure = gds_forms.GovUKRadioInputField(
        choices=YesNoChoices.choices,
        gds_field_kwargs=gds_forms.FIELDSET_LEGEND_HEADER,
        error_messages={"required": "Select yes or no"},
    )

    def __init__(self, *args: Any, country: Country, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.country = country
        self.fields["are_you_sure"].label = f"Are you sure you want to remove {country}?"


def get_user_editable_exporters(user: User) -> QuerySet[Exporter]:
    """Main exporters the user can edit or is an agent of.

    This is a list of the following:
        - Exporters where user has the edit permission on the main exporter.
        - Exporters that the user is an agent of.
    """

    return get_objects_for_user(
        user,
        [Perms.obj.exporter.edit, Perms.obj.exporter.is_agent],
        Exporter.objects.filter(is_active=True, main_exporter__isnull=True),
        any_perm=True,
    )


def get_user_agent_exporters(user: User) -> QuerySet[Exporter]:
    """Return exporters that the user is an agent of."""

    return get_objects_for_user(
        user,
        [Perms.obj.exporter.edit],
        Exporter.objects.filter(is_active=True, main_exporter__isnull=False),
    )


def get_exporter_choices(
    exporters: QuerySet[Exporter], include_none_of_these: bool = True
) -> list[tuple[int | str, Markup | str]]:
    exporter_list: list[tuple[int | str, Markup | str]] = [(c.pk, c.name) for c in exporters]

    if include_none_of_these:
        exporter_list.append((gds_forms.GovUKRadioInputField.NONE_OF_THESE, "Another company"))

    return exporter_list


def get_user_offices(user: User, chosen_exporter: Exporter | None) -> QuerySet[Office]:
    # Main exporters the user can edit or is an agent of filtered by the chosen exporter.

    if chosen_exporter:
        exporter = get_user_editable_exporters(user).filter(pk=chosen_exporter.pk).first()
    else:
        exporter = None

    if exporter:
        return exporter.offices.filter(is_active=True)
    else:
        return Office.objects.none()


def get_office_choices(
    offices: QuerySet[Office], include_none_of_these: bool = True
) -> list[tuple[int | str, Markup | str]]:

    office_list: list[tuple[int | str, Markup | str]] = [
        (o.pk, _get_address_label(o)) for o in offices
    ]

    if include_none_of_these:
        office_list.append((gds_forms.GovUKRadioInputField.NONE_OF_THESE, "Another office address"))

    return office_list


def _get_address_label(office: Office) -> Markup:
    """Join the address property (all address fields) with the postcode.

    All fields are escaped, as it's user entered data before being returned as safe Markup to
    render as HTML by the GDS field macro.
    """

    address = office.address
    if office.postcode:
        address += f"\n{office.postcode}"

    return Markup("<br>".join([escape(line) for line in address.split("\n")]))
