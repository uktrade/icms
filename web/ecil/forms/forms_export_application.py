from typing import Any

from django.db.models import QuerySet
from guardian.shortcuts import get_objects_for_user
from markupsafe import Markup, escape

from web.ecil.gds import forms as gds_forms
from web.ecil.types import EXPORT_APPLICATION
from web.models import Country, ECILUserExportApplication, Exporter, Office, User
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


class ExportApplicationExportCountriesForm(gds_forms.GDSForm):
    # Can't use a ModelForm here as "countries" is a ManyToMany model field.
    # There are no GDS components that can render a select multiple form field.
    # Therefore, it's cleaner to create a GDSForm and save the data in the view.
    countries = gds_forms.GovUKSelectField(
        label="Where do you want to export products to?",
        help_text=(
            "Enter a country or territory and select from the results."
            " You can add up to 40 countries or territories."
        ),
        choices=[],
        gds_field_kwargs=gds_forms.LABEL_HEADER,
        error_messages={"required": "Select a country or territory you want to export to"},
    )

    def __init__(self, *args: Any, instance: EXPORT_APPLICATION, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.instance = instance
        self.selected_countries = self.instance.countries.all()

        countries = [(None, "")] + list(Country.app.get_cfs_countries().values_list("id", "name"))
        self.fields["countries"].choices = countries

    def clean_countries(self) -> Country | None:
        if country_pk := self.cleaned_data.get("countries"):
            return Country.app.get_cfs_countries().get(pk=country_pk)

        return None

    def clean(self) -> None:
        cleaned_data = super().clean()

        if (
            self.selected_countries
            and cleaned_data.get("countries")
            and len(self.selected_countries) >= 40
        ):
            self.add_error("countries", "You can only add up to 40 countries or territories")

        return cleaned_data


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
