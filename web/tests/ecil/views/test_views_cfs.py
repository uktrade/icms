from http import HTTPStatus

import pytest
from django.http import HttpResponse
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertTemplateUsed

from web.ecil.gds.forms import fields
from web.models import (
    CertificateOfFreeSaleApplication,
    CFSProduct,
    CFSSchedule,
    Country,
    ProductLegislation,
)
from web.models.shared import AddressEntryType, YesNoChoices


def assert_back_link_url(
    response: HttpResponse, expected_url: str, expected_text: str = "Back"
) -> None:
    back_link_kwargs = response.context["back_link_kwargs"]

    actual_text = back_link_kwargs["text"]
    assert expected_text == actual_text

    actual_url = back_link_kwargs["href"]
    assert expected_url == actual_url


def get_cfs_url(view_name: str, app: CertificateOfFreeSaleApplication) -> str:
    return reverse(view_name, kwargs={"application_pk": app.pk})


def get_cfs_schedule_url(
    view_name: str, app: CertificateOfFreeSaleApplication, schedule: CFSSchedule
) -> str:
    return reverse(view_name, kwargs={"application_pk": app.pk, "schedule_pk": schedule.pk})


def get_cfs_schedule_product_url(
    view_name: str,
    app: CertificateOfFreeSaleApplication,
    schedule: CFSSchedule,
    product: CFSProduct,
) -> str:
    return reverse(
        view_name,
        kwargs={"application_pk": app.pk, "schedule_pk": schedule.pk, "product_pk": product.pk},
    )


class TestCFSApplicationReferenceUpdateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_export_user, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.url = get_cfs_url("ecil:export-cfs:application-reference", self.app)
        self.client = prototype_export_client

    def test_permission(self, exporter_two_client):
        response = exporter_two_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/gds_form.html")

        assert response.context["back_link_kwargs"] == {
            "text": "Back",
            "href": reverse("workbasket"),
        }

    def test_post(self):
        # Test optional is valid
        form_data = {"applicant_reference": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == get_cfs_url("ecil:export-cfs:application-contact", self.app)

        # Test post success
        form_data = {"applicant_reference": "test-application-reference"}
        response = self.client.post(self.url, data=form_data)

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == get_cfs_url("ecil:export-cfs:application-contact", self.app)

        self.app.refresh_from_db()
        assert self.app.applicant_reference == "test-application-reference"


class TestCFSApplicationContactUpdateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_export_user, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.user = prototype_export_user
        self.url = get_cfs_url("ecil:export-cfs:application-contact", self.app)
        self.client = prototype_export_client

    def test_permission(self, exporter_two_client):
        response = exporter_two_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/gds_form.html")

        assert response.context["back_link_kwargs"] == {
            "text": "Back",
            "href": get_cfs_url("ecil:export-cfs:application-reference", self.app),
        }

    def test_post(self):
        # Test error message
        form_data = {"contact": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "contact": ["Select the main contact for your application"],
        }

        # Test post success when picking user
        form_data = {"contact": str(self.user.pk)}
        response = self.client.post(self.url, data=form_data)

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == get_cfs_url("ecil:export-application:countries", self.app)

        # Test having an existing country changes the post redirect.
        self.app.countries.add(Country.app.get_cfs_countries().first())

        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == get_cfs_url(
            "ecil:export-application:countries-add-another", self.app
        )

        self.app.refresh_from_db()
        assert self.app.contact == self.user

        # Test post success when picking "Someone else"
        form_data = {"contact": fields.GovUKRadioInputField.NONE_OF_THESE}
        response = self.client.post(self.url, data=form_data)

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("ecil:export-application:another-contact")

        self.app.refresh_from_db()
        assert self.app.contact is None


class TestCFSScheduleCreateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_export_user, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.url = get_cfs_url("ecil:export-cfs:schedule-create", self.app)
        self.client = prototype_export_client

    def test_permission(self, exporter_two_client):
        response = exporter_two_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/cfs/schedule_create.html")

        expected_url = get_cfs_url("ecil:export-application:countries", self.app)
        assert_back_link_url(response, expected_url)

        assert response.context["create_schedule_btn_kwargs"] == {
            "text": "Create a product schedule",
            "type": "submit",
            "isStartButton": True,
            "preventDoubleClick": True,
        }

    def test_post(self):
        assert self.app.schedules.count() == 1

        # Test post success
        response = self.client.post(self.url)

        self.app.refresh_from_db()
        assert self.app.schedules.count() == 2

        assert response.status_code == HTTPStatus.FOUND

        expected_url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-exporter-status", self.app, self.app.schedules.last()
        )
        assert response.url == expected_url


class TestCFSScheduleExporterStatusUpdateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.schedule = prototype_cfs_app_in_progress.schedules.first()
        self.url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-exporter-status", self.app, self.schedule
        )
        self.client = prototype_export_client

    def test_permission(self, exporter_two_client):
        response = exporter_two_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/gds_form.html")

        expected_url = get_cfs_url("ecil:export-cfs:schedule-create", self.app)
        assert_back_link_url(response, expected_url)

    def test_post(self):
        # Test error message
        form_data = {"exporter_status": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "exporter_status": ["Select yes or no"],
        }

        # Check record exists but no app type set
        assert self.schedule.exporter_status is None

        # Test post success
        form_data = {"exporter_status": CFSSchedule.ExporterStatus.IS_MANUFACTURER}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == get_cfs_schedule_url(
            "ecil:export-cfs:schedule-manufacturer-address", self.app, self.schedule
        )

        self.schedule.refresh_from_db()
        assert self.schedule.exporter_status == CFSSchedule.ExporterStatus.IS_MANUFACTURER


class TestCFSScheduleManufacturerAddressUpdateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.schedule = prototype_cfs_app_in_progress.schedules.first()
        self.url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-manufacturer-address", self.app, self.schedule
        )
        self.client = prototype_export_client

    def test_permission(self, exporter_two_client):
        response = exporter_two_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/cfs/schedule_manufacturer_address.html")

        expected_url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-exporter-status", self.app, self.schedule
        )
        assert_back_link_url(response, expected_url)

        # Check custom header is present
        html = response.content.decode("utf-8")
        assertInHTML(
            """
            <h1 class="govuk-heading-l">
                <span class="govuk-caption-l">
                    Product schedule 1
                </span>
                What is the manufacturer name and address? (Optional)
              </h1>
            """,
            html,
        )

    def test_post(self):
        # Test everything is optional
        form_data = {
            "manufacturer_name": "",
            "manufacturer_postcode": "",
            "manufacturer_address": "",
        }
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND

        # Check record exists but no manufacturer address fields set
        self.schedule.refresh_from_db()
        assert self.schedule.manufacturer_name is None
        assert self.schedule.manufacturer_postcode is None
        assert self.schedule.manufacturer_address == ""
        # Should be set to manual until we implement postcode search
        assert self.schedule.manufacturer_address_entry_type == AddressEntryType.MANUAL

        # Test post success
        form_data = {
            "manufacturer_name": "Test manufacturer name",
            "manufacturer_postcode": "S12SS",  # /PS-IGNORE
            "manufacturer_address": "Test manufacturer address",
        }
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND

        assert response.url == get_cfs_schedule_url(
            "ecil:export-cfs:schedule-brand-name-holder", self.app, self.schedule
        )

        self.schedule.refresh_from_db()
        assert self.schedule.manufacturer_name == "Test manufacturer name"
        assert self.schedule.manufacturer_postcode == "S12SS"  # /PS-IGNORE
        assert self.schedule.manufacturer_address == "Test manufacturer address"
        assert self.schedule.manufacturer_address_entry_type == AddressEntryType.MANUAL


class TestCFSScheduleBrandNameHolderUpdateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.schedule = prototype_cfs_app_in_progress.schedules.first()
        self.url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-brand-name-holder", self.app, self.schedule
        )
        self.client = prototype_export_client

    def test_permission(self, exporter_two_client):
        response = exporter_two_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/gds_form.html")

        expected_url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-manufacturer-address", self.app, self.schedule
        )
        assert_back_link_url(response, expected_url)

        # Check custom header is present
        html = response.content.decode("utf-8")
        assertInHTML(
            """
            <h1 class="govuk-fieldset__heading">
              <span class="govuk-caption-l">Product schedule 1</span>
              Is the company the brand name holder for the product?
            </h1>
            """,
            html,
        )

    def test_post(self):
        # Test error message
        form_data = {"brand_name_holder": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "brand_name_holder": ["Select yes or no"],
        }

        # Check record exists but no brand holder name set
        assert self.schedule.brand_name_holder is None

        # Test post success
        form_data = {"brand_name_holder": YesNoChoices.yes}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND

        assert response.url == get_cfs_schedule_url(
            "ecil:export-cfs:schedule-country-of-manufacture", self.app, self.schedule
        )

        self.schedule.refresh_from_db()
        assert self.schedule.brand_name_holder == YesNoChoices.yes


class TestCFSScheduleCountryOfManufactureUpdateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.schedule = prototype_cfs_app_in_progress.schedules.first()
        self.url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-country-of-manufacture", self.app, self.schedule
        )
        self.client = prototype_export_client

    def test_permission(self, exporter_two_client):
        response = exporter_two_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/cfs/schedule_country_of_manufacture.html")

        expected_url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-brand-name-holder", self.app, self.schedule
        )
        assert_back_link_url(response, expected_url)

        # Check custom header is present
        html = response.content.decode("utf-8")
        assertInHTML(
            """
            <h1 class="govuk-label-wrapper">
              <label class="govuk-label govuk-label--l" for="id_country_of_manufacture">
                <span class="govuk-caption-l">Product schedule 1</span>Where is the product manufactured?
              </label>
            </h1>
            """,
            html,
        )

    def test_post(self):
        # Test error message
        form_data = {"country_of_manufacture": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "country_of_manufacture": ["Add a country or territory"],
        }

        # Check record exists but no country of manufacture name set
        assert self.schedule.country_of_manufacture is None

        # Test post success
        valid_country = Country.app.get_cfs_com_countries().first()
        form_data = {"country_of_manufacture": valid_country.pk}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND

        assert response.url == get_cfs_schedule_url(
            "ecil:export-cfs:schedule-legislation", self.app, self.schedule
        )

        self.schedule.refresh_from_db()
        assert self.schedule.country_of_manufacture == valid_country

        # Test having an existing legislation changes the post redirect.
        self.schedule.legislations.add(
            ProductLegislation.objects.filter(is_active=True, gb_legislation=True).first()
        )
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == get_cfs_schedule_url(
            "ecil:export-cfs:schedule-legislation-add-another", self.app, self.schedule
        )


class TestCFSScheduleAddLegislationUpdateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.schedule = prototype_cfs_app_in_progress.schedules.first()
        self.url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-legislation", self.app, self.schedule
        )
        self.client = prototype_export_client

    def test_permission(self, exporter_two_client):
        response = exporter_two_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self, exporter_site):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/cfs/schedule_legislation.html")

        expected_url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-country-of-manufacture", self.app, self.schedule
        )
        assert_back_link_url(response, expected_url)

        # Check custom header is present
        html = response.content.decode("utf-8")
        assertInHTML(
            """
            <h1 class="govuk-label-wrapper">
                <label class="govuk-label govuk-label--l" for="id_legislations">
                    <span class="govuk-caption-l">Product schedule 1</span>Which legislation applies to the product?
                </label>
            </h1>
            """,
            html,
        )

        # Test referrer back link is correct.
        referrer = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-legislation-add-another", self.app, self.schedule
        )
        headers = {"REFERER": f"http://{exporter_site.domain}{referrer}"}
        response = self.client.get(self.url, headers=headers)
        assert response.status_code == HTTPStatus.OK
        assert response.context["back_link_kwargs"]["href"] == referrer

        # Test having an existing legislation changes the title.
        self.schedule.legislations.add(
            ProductLegislation.objects.filter(is_active=True, gb_legislation=True).first()
        )
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        html = response.content.decode("utf-8")
        assertInHTML(
            """
            <h1 class="govuk-label-wrapper">
                <label class="govuk-label govuk-label--l" for="id_legislations">
                    <span class="govuk-caption-l">Product schedule 1</span>Add another legislation
                </label>
            </h1>
            """,
            html,
        )

    def test_post(self):
        # Test error message
        form_data = {"legislations": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "legislations": ["Add a legislation that applies to the product"],
        }

        # Check record exists but no country of manufacture name set
        assert self.schedule.legislations.count() == 0

        # Test post success
        valid_legislation = form.fields["legislations"].queryset.first()
        form_data = {"legislations": valid_legislation.pk}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == get_cfs_schedule_url(
            "ecil:export-cfs:schedule-legislation-add-another", self.app, self.schedule
        )

        self.schedule.refresh_from_db()
        assert self.schedule.legislations.count() == 1
        assert self.schedule.legislations.first() == valid_legislation

        # Test limit of adding 3 legislations (already linked to one)
        l2, l3, l4 = form.fields["legislations"].queryset[2:5]

        form_data = {"legislations": l2.pk}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND

        form_data = {"legislations": l3.pk}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND

        form_data = {"legislations": l4.pk}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "legislations": ["You can only add up to 3 legislations"],
        }


class TestCFSScheduleAddAnotherLegislationFormView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.schedule = prototype_cfs_app_in_progress.schedules.first()
        self.available_legislations = ProductLegislation.objects.filter(
            is_active=True, gb_legislation=True
        )
        self.schedule.legislations.add(*self.available_legislations[:2])
        self.url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-legislation-add-another", self.app, self.schedule
        )
        self.client = prototype_export_client

    def test_permission(self, exporter_two_client):
        response = exporter_two_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/cfs/schedule_legislation_add_another.html")

        expected_url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-legislation", self.app, self.schedule
        )
        assert_back_link_url(response, expected_url)

        # Check custom header is present
        html = response.content.decode("utf-8")
        assertInHTML(
            """
              <h1 class="govuk-heading-l">
                <span class="govuk-caption-l">Product schedule 1</span>You have added 2 legislations
              </h1>
            """,
            html,
        )

        # Check list_with_actions_kwargs
        l1, l2 = self.available_legislations[:2]
        assert response.context["list_with_actions_kwargs"] == {
            "rows": [
                {
                    "name": l1.name,
                    "actions": [
                        {
                            "label": "Remove",
                            "url": reverse(
                                "ecil:export-cfs:schedule-legislation-remove",
                                kwargs={
                                    "application_pk": self.app.pk,
                                    "schedule_pk": self.schedule.pk,
                                    "legislation_pk": l1.pk,
                                },
                            ),
                        }
                    ],
                },
                {
                    "name": l2.name,
                    "actions": [
                        {
                            "label": "Remove",
                            "url": reverse(
                                "ecil:export-cfs:schedule-legislation-remove",
                                kwargs={
                                    "application_pk": self.app.pk,
                                    "schedule_pk": self.schedule.pk,
                                    "legislation_pk": l2.pk,
                                },
                            ),
                        }
                    ],
                },
            ]
        }

    def test_post(self):
        # Test error message
        form_data = {"add_another": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "add_another": ["Select yes or no"],
        }

        # Test post success (yes)
        form_data = {"add_another": YesNoChoices.yes}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == get_cfs_schedule_url(
            "ecil:export-cfs:schedule-legislation", self.app, self.schedule
        )

        # Test post success (no)
        form_data = {"add_another": YesNoChoices.no}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == get_cfs_schedule_url(
            "ecil:export-cfs:schedule-product-standard", self.app, self.schedule
        )


class TestCFSScheduleConfirmRemoveLegislationFormView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.schedule = prototype_cfs_app_in_progress.schedules.first()
        available_legislations = ProductLegislation.objects.filter(
            is_active=True, gb_legislation=True
        )
        self.schedule.legislations.add(*available_legislations[:2])
        self.client = prototype_export_client
        self.legislation = self.schedule.legislations.first()
        self.url = reverse(
            "ecil:export-cfs:schedule-legislation-remove",
            kwargs={
                "application_pk": self.app.pk,
                "schedule_pk": self.schedule.pk,
                "legislation_pk": self.legislation.pk,
            },
        )

    def test_permission(self, exporter_two_client):
        response = exporter_two_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/gds_form.html")

        expected_url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-legislation-add-another", self.app, self.schedule
        )
        assert_back_link_url(response, expected_url)

        # Check custom header is present
        html = response.content.decode("utf-8")
        assertInHTML(
            """
              <h1 class="govuk-fieldset__heading">
                <span class="govuk-caption-l">Product schedule 1</span>Are you sure you want to remove this legislation?
              </h1>
            """,
            html,
        )
        # Check leslation text is present.
        assertInHTML(f"""<div class="govuk-inset-text">{self.legislation.name}</div>""", html)

    def test_post(self):
        # Test error message
        form_data = {"are_you_sure": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "are_you_sure": ["Select yes or no"],
        }

        # Test post success (no)
        assert self.schedule.legislations.count() == 2
        form_data = {"are_you_sure": YesNoChoices.no}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == get_cfs_schedule_url(
            "ecil:export-cfs:schedule-legislation-add-another", self.app, self.schedule
        )
        assert self.schedule.legislations.count() == 2

        # Test post success (yes)
        form_data = {"are_you_sure": YesNoChoices.yes}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == get_cfs_schedule_url(
            "ecil:export-cfs:schedule-legislation-add-another", self.app, self.schedule
        )
        assert self.schedule.legislations.count() == 1

        # Test removing last legislation redirects to correct view.
        legislation = self.schedule.legislations.first()
        url = reverse(
            "ecil:export-cfs:schedule-legislation-remove",
            kwargs={
                "application_pk": self.app.pk,
                "schedule_pk": self.schedule.pk,
                "legislation_pk": legislation.pk,
            },
        )
        form_data = {"are_you_sure": YesNoChoices.yes}
        response = self.client.post(url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == get_cfs_schedule_url(
            "ecil:export-cfs:schedule-legislation", self.app, self.schedule
        )
        assert self.schedule.legislations.count() == 0


class TestCFSScheduleProductStandardUpdateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.schedule = prototype_cfs_app_in_progress.schedules.first()

        self.url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-product-standard", self.app, self.schedule
        )
        self.client = prototype_export_client

    def test_permission(self, exporter_two_client):
        response = exporter_two_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/gds_form.html")

        expected_url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-legislation", self.app, self.schedule
        )
        assert_back_link_url(response, expected_url)

        # Check custom header is present
        html = response.content.decode("utf-8")
        assertInHTML(
            """
              <h1 class="govuk-fieldset__heading">
                <span class="govuk-caption-l">Product schedule 1</span>Which statement applies to the product?
              </h1>
            """,
            html,
        )

        # Having existing legislation should change the back link.
        self.schedule.legislations.add(
            ProductLegislation.objects.filter(is_active=True, gb_legislation=True).first()
        )
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        expected_url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-legislation-add-another", self.app, self.schedule
        )
        assert_back_link_url(response, expected_url)

    def test_post(self):
        # Test error message
        form_data = {"product_standard": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "product_standard": ["Select a statement"],
        }

        # Check record exists but no country of manufacture name set
        assert self.schedule.product_standard == ""

        # Test post success (PRODUCT_SOLD_ON_UK_MARKET)
        form_data = {"product_standard": CFSSchedule.ProductStandards.PRODUCT_SOLD_ON_UK_MARKET}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == get_cfs_schedule_url(
            "ecil:export-cfs:schedule-accordance-with-standards", self.app, self.schedule
        )

        self.schedule.refresh_from_db()
        assert (
            self.schedule.product_standard == CFSSchedule.ProductStandards.PRODUCT_SOLD_ON_UK_MARKET
        )
        assert self.schedule.product_eligibility == CFSSchedule.ProductEligibility.SOLD_ON_UK_MARKET
        assert self.schedule.goods_placed_on_uk_market == YesNoChoices.yes
        assert self.schedule.goods_export_only == YesNoChoices.no

        # Test post success (PRODUCT_FUTURE_UK_MARKET)
        form_data = {"product_standard": CFSSchedule.ProductStandards.PRODUCT_FUTURE_UK_MARKET}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND

        assert response.url == get_cfs_schedule_url(
            "ecil:export-cfs:schedule-accordance-with-standards", self.app, self.schedule
        )

        self.schedule.refresh_from_db()
        assert (
            self.schedule.product_standard == CFSSchedule.ProductStandards.PRODUCT_FUTURE_UK_MARKET
        )
        assert (
            self.schedule.product_eligibility
            == CFSSchedule.ProductEligibility.MEET_UK_PRODUCT_SAFETY
        )
        assert self.schedule.goods_placed_on_uk_market == YesNoChoices.yes
        assert self.schedule.goods_export_only == YesNoChoices.no

        # Test post success (PRODUCT_EXPORT_ONLY)
        form_data = {"product_standard": CFSSchedule.ProductStandards.PRODUCT_EXPORT_ONLY}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == get_cfs_schedule_url(
            "ecil:export-cfs:schedule-accordance-with-standards", self.app, self.schedule
        )

        self.schedule.refresh_from_db()
        assert self.schedule.product_standard == CFSSchedule.ProductStandards.PRODUCT_EXPORT_ONLY
        assert (
            self.schedule.product_eligibility
            == CFSSchedule.ProductEligibility.MEET_UK_PRODUCT_SAFETY
        )
        assert self.schedule.goods_placed_on_uk_market == YesNoChoices.no
        assert self.schedule.goods_export_only == YesNoChoices.yes

        # Test eu_cosmetic_regulation redirects to correct schedule statement view.
        self.schedule.legislations.add(
            ProductLegislation.objects.filter(
                is_active=True,
                gb_legislation=True,
                is_eu_cosmetics_regulation=True,
            ).first()
        )

        form_data = {"product_standard": CFSSchedule.ProductStandards.PRODUCT_SOLD_ON_UK_MARKET}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == get_cfs_schedule_url(
            "ecil:export-cfs:schedule-is-responsible-person", self.app, self.schedule
        )


class TestCFSScheduleStatementIsResponsiblePersonUpdateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.schedule = prototype_cfs_app_in_progress.schedules.first()
        self.schedule.goods_export_only = YesNoChoices.no
        self.schedule.save()

        self.url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-is-responsible-person", self.app, self.schedule
        )
        self.client = prototype_export_client
        self.gb_eu_cosmetic_legislation = ProductLegislation.objects.filter(
            is_active=True, gb_legislation=True, is_eu_cosmetics_regulation=True
        ).first()

    def test_permission(self, exporter_two_client):
        response = exporter_two_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        # Test correct client doesn't have permission without the requited legislation.
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        # Add a GB legislation
        self.schedule.legislations.add(self.gb_eu_cosmetic_legislation)
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        # Add a GB legislation
        self.schedule.legislations.add(self.gb_eu_cosmetic_legislation)

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/gds_form.html")

        expected_url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-product-standard", self.app, self.schedule
        )
        assert_back_link_url(response, expected_url)

        # Check custom header is present
        html = response.content.decode("utf-8")
        assertInHTML(
            """
              <h1 class="govuk-fieldset__heading">
                <span class="govuk-caption-l">Product schedule 1</span>Are you the responsible person for the product?
              </h1>
            """,
            html,
        )

        # Check legislation is in html
        assertInHTML("Cosmetic Regulation No 1223/2009 as applicable in GB", html)

        # Check NI legislation changes html
        self.schedule.legislations.remove(self.gb_eu_cosmetic_legislation)
        self.schedule.legislations.add(
            ProductLegislation.objects.filter(
                is_active=True, ni_legislation=True, is_eu_cosmetics_regulation=True
            ).first()
        )

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/gds_form.html")
        html = response.content.decode("utf-8")
        assertInHTML(
            "Regulation (EC) No 1223/2009 of the European Parliament and of the Council of 30 November 2009 on cosmetic products as applicable in NI",
            html,
        )

    def test_post(self):
        # Test error message
        self.schedule.legislations.add(self.gb_eu_cosmetic_legislation)
        form_data = {"schedule_statements_is_responsible_person": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "schedule_statements_is_responsible_person": ["Select yes or no"],
        }

        # Check schedule_statements_is_responsible_person is set to default.
        assert self.schedule.schedule_statements_is_responsible_person is False

        # Test post success
        form_data = {"schedule_statements_is_responsible_person": "True"}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == get_cfs_schedule_url(
            "ecil:export-cfs:schedule-accordance-with-standards", self.app, self.schedule
        )

        self.schedule.refresh_from_db()
        assert self.schedule.schedule_statements_is_responsible_person is True


class TestCFSScheduleStatementAccordanceWithStandardsUpdateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.schedule = prototype_cfs_app_in_progress.schedules.first()
        self.url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-accordance-with-standards", self.app, self.schedule
        )
        self.client = prototype_export_client

    def test_permission(self, exporter_two_client):
        response = exporter_two_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/gds_form.html")

        expected_url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-product-standard", self.app, self.schedule
        )
        assert_back_link_url(response, expected_url)

        # Check custom header is present
        html = response.content.decode("utf-8")
        assertInHTML(
            """
              <h1 class="govuk-fieldset__heading">
                <span class="govuk-caption-l">Product schedule 1</span>
                Are these products manufactured in accordance with the Good Manufacturing Practice standards set out in UK law?
              </h1>
            """,
            html,
        )

        # Check adding a cosmetic legislation changes the back link.
        self.schedule.legislations.add(
            ProductLegislation.objects.filter(
                is_active=True, gb_legislation=True, is_eu_cosmetics_regulation=True
            ).first()
        )
        self.schedule.goods_export_only = YesNoChoices.no
        self.schedule.save()

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/gds_form.html")

        expected_url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-is-responsible-person", self.app, self.schedule
        )
        assert_back_link_url(response, expected_url)

    def test_post(self):
        # Test error message
        form_data = {"schedule_statements_accordance_with_standards": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "schedule_statements_accordance_with_standards": ["Select yes or no"],
        }

        # Check schedule_statements_accordance_with_standards is set to default.
        assert self.schedule.schedule_statements_accordance_with_standards is False

        # Test post success
        form_data = {"schedule_statements_accordance_with_standards": "True"}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == get_cfs_schedule_url(
            "ecil:export-cfs:schedule-product-start", self.app, self.schedule
        )

        self.schedule.refresh_from_db()
        assert self.schedule.schedule_statements_accordance_with_standards is True


class TestCFSScheduleAddProductStartTemplateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.schedule = prototype_cfs_app_in_progress.schedules.first()
        self.url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-product-start", self.app, self.schedule
        )
        self.client = prototype_export_client

    def test_permission(self, exporter_two_client):
        response = exporter_two_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/cfs/schedule_product_start.html")

        context = response.context

        expected_url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-accordance-with-standards", self.app, self.schedule
        )
        assert_back_link_url(response, expected_url)

        assert context["next_url"] == get_cfs_schedule_url(
            "ecil:export-cfs:schedule-product-add-method", self.app, self.schedule
        )

        assert context["details_kwargs"] == {
            "text": (
                "Products included in kits need to be listed individually."
                " Some products may need different legislations."
                " For example, if a kit includes toner, moisturiser and a hairbrush,"
                " the hairbrush would require a separate legislation as it is not a cosmetic product."
            ),
            "summaryText": "The product is part of a kit",
        }

        # Check custom header is present
        html = response.content.decode("utf-8")
        assertInHTML(
            """
              <h1 class="govuk-heading-l">
                <span class="govuk-caption-l">Product schedule 1</span>Add product details
              </h1>
            """,
            html,
        )

    def test_post_forbidden(self):
        response = self.client.post(self.url)

        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


class TestCFSScheduleProductAddMethodFormView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.schedule = prototype_cfs_app_in_progress.schedules.first()
        self.url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-product-add-method", self.app, self.schedule
        )
        self.client = prototype_export_client

    def test_permission(self, exporter_two_client):
        response = exporter_two_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/gds_form.html")

        expected_url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-product-start", self.app, self.schedule
        )
        assert_back_link_url(response, expected_url)

        # Check custom header is present
        html = response.content.decode("utf-8")
        assertInHTML(
            """
              <h1 class="govuk-fieldset__heading">
                <span class="govuk-caption-l">Product schedule 1</span>How do you want to add products?
              </h1>
            """,
            html,
        )

    def test_post(self):
        # Test error message
        form_data = {"method": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "method": ["Select how you want to add your products"],
        }

        # Test post success (manual)
        form_data = {"method": "manual"}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == get_cfs_schedule_url(
            "ecil:export-cfs:schedule-product-add", self.app, self.schedule
        )

        # Test post success (in bulk)
        form_data = {"method": "in_bulk"}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == get_cfs_schedule_url(
            "export:cfs-schedule-edit", self.app, self.schedule
        )


class TestCFSScheduleProductCreateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.schedule = prototype_cfs_app_in_progress.schedules.first()
        self.url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-product-add", self.app, self.schedule
        )
        self.client = prototype_export_client

    def test_permission(self, exporter_two_client):
        response = exporter_two_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/cfs/schedule_product_add.html")

        expected_url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-product-add-method", self.app, self.schedule
        )
        assert_back_link_url(response, expected_url)

        # Check custom header is present
        html = response.content.decode("utf-8")
        assertInHTML(
            """
            <h1 class="govuk-heading-l">
              <span class="govuk-caption-l">Product schedule 1</span>
              Add a product
            </h1>
            """,
            html,
        )

    def test_post(self):
        # Test error message
        form_data = {"product_name": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {"product_name": ["Add a product name"]}

        # Check no products exist yet
        assert self.schedule.products.count() == 0

        # Test post success
        form_data = {"product_name": "Test product 1"}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND

        # Check a product has been added
        assert self.schedule.products.count() == 1
        product = self.schedule.products.first()
        assert product.product_name == "Test product 1"
        assert not product.is_raw_material
        assert response.url == get_cfs_schedule_product_url(
            "ecil:export-cfs:schedule-product-end-use", self.app, self.schedule, product
        )

        #
        # Test adding a raw material product
        #
        form_data = {"product_name": "Test product 2", "is_raw_material": "True"}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND

        # Check a product has been added
        assert self.schedule.products.count() == 2
        product = self.schedule.products.last()
        assert product.product_name == "Test product 2"
        assert product.is_raw_material
        assert response.url == get_cfs_schedule_product_url(
            "ecil:export-cfs:schedule-product-end-use", self.app, self.schedule, product
        )

    def test_duplicate_product_name_error(self):
        form_data = {"product_name": "Test product 1"}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND

        # Check a product has been added
        assert self.schedule.products.count() == 1

        form_data = {"product_name": "Test product 1"}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {"product_name": ["Product name must be unique to the schedule."]}


class TestCFSScheduleProductUpdateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.schedule = prototype_cfs_app_in_progress.schedules.first()
        self.product = self.schedule.products.create(product_name="Test product")
        self.url = get_cfs_schedule_product_url(
            "ecil:export-cfs:schedule-product-edit", self.app, self.schedule, self.product
        )
        self.client = prototype_export_client

    def test_permission(self, exporter_two_client):
        response = exporter_two_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/cfs/schedule_product_add.html")

        expected_url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-product-add-another", self.app, self.schedule
        )
        assert_back_link_url(response, expected_url)

        # Check custom header is present
        html = response.content.decode("utf-8")
        assertInHTML(
            """
            <h1 class="govuk-heading-l">
              <span class="govuk-caption-l">Product schedule 1</span>
              Add a product
            </h1>
            """,
            html,
        )

    def test_post(self):
        # Test error message
        form_data = {"product_name": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {"product_name": ["Add a product name"]}

        # Check one product exists already
        assert self.schedule.products.count() == 1

        # Test post success
        form_data = {"product_name": "Test product 1 updated"}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND

        # Check the product has been updated
        assert self.schedule.products.count() == 1

        self.product.refresh_from_db()

        assert self.product.product_name == "Test product 1 updated"
        assert not self.product.is_raw_material
        assert response.url == get_cfs_schedule_product_url(
            "ecil:export-cfs:schedule-product-end-use", self.app, self.schedule, self.product
        )

        #
        # Test raw material product
        #
        form_data = {"product_name": "Test product 1", "is_raw_material": "True"}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND

        # Check the product has been updated
        assert self.schedule.products.count() == 1
        self.product.refresh_from_db()

        assert self.product.product_name == "Test product 1"
        assert self.product.is_raw_material
        assert response.url == get_cfs_schedule_product_url(
            "ecil:export-cfs:schedule-product-end-use", self.app, self.schedule, self.product
        )

    def test_duplicate_product_name_error(self):
        assert self.schedule.products.count() == 1
        # Create another product to test a duplicate
        self.schedule.products.create(product_name="Test product 2")

        form_data = {"product_name": "Test product 2"}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {"product_name": ["Product name must be unique to the schedule."]}


class TestCFSScheduleProductEndUseUpdateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.schedule = prototype_cfs_app_in_progress.schedules.first()
        self.product = self.schedule.products.create(product_name="Test product")
        self.url = get_cfs_schedule_product_url(
            "ecil:export-cfs:schedule-product-end-use", self.app, self.schedule, self.product
        )
        self.client = prototype_export_client

    def test_permission(self, exporter_two_client):
        response = exporter_two_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/gds_form.html")

        expected_url = get_cfs_schedule_product_url(
            "ecil:export-cfs:schedule-product-edit", self.app, self.schedule, self.product
        )
        assert_back_link_url(response, expected_url)

        # Check custom header is present
        html = response.content.decode("utf-8")
        assertInHTML(
            """
            <h1 class="govuk-label-wrapper">
                <label class="govuk-label govuk-label--l" for="id_product_end_use">
                    <span class="govuk-caption-l">Product schedule 1</span>What is Test product used for? (Optional)
                </label>
            </h1>
            """,
            html,
        )

        # Check raw material has a different header.
        self.product.is_raw_material = True
        self.product.save()

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/gds_form.html")

        expected_url = get_cfs_schedule_product_url(
            "ecil:export-cfs:schedule-product-edit", self.app, self.schedule, self.product
        )
        assert_back_link_url(response, expected_url)

        # Check custom header is present
        html = response.content.decode("utf-8")
        assertInHTML(
            """
            <h1 class="govuk-label-wrapper">
                <label class="govuk-label govuk-label--l" for="id_product_end_use">
                    <span class="govuk-caption-l">Product schedule 1</span>What is the finished product use for Test product?
                </label>
            </h1>
            """,
            html,
        )

    def test_post(self):
        # Test field optional for non-raw material
        form_data = {"product_end_use": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == get_cfs_schedule_url(
            "ecil:export-cfs:schedule-product-add-another", self.app, self.schedule
        )

        # Test required error for required product
        self.product.is_raw_material = True
        self.product.save()

        form_data = {"product_end_use": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {"product_end_use": ["Enter a finished product use"]}

        # Test post success
        form_data = {"product_end_use": "Test product end use."}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == get_cfs_schedule_url(
            "ecil:export-cfs:schedule-product-add-another", self.app, self.schedule
        )

        self.product.refresh_from_db()
        assert self.product.product_end_use == "Test product end use."


class TestCFSScheduleProductAddAnotherFormView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.schedule = prototype_cfs_app_in_progress.schedules.first()
        self.p1 = self.schedule.products.create(
            product_name="Test product 1",
        )
        self.p2 = self.schedule.products.create(
            product_name="Test product 2",
            is_raw_material=True,
            product_end_use="Test product end use",
        )

        self.url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-product-add-another", self.app, self.schedule
        )
        self.client = prototype_export_client

    def test_permission(self, exporter_two_client):
        response = exporter_two_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/cfs/schedule_product_add_another.html")

        expected_url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-product-add-method", self.app, self.schedule
        )
        assert_back_link_url(response, expected_url)

        # Check custom header is present
        html = response.content.decode("utf-8")
        assertInHTML(
            """
              <h1 class="govuk-heading-l">
                <span class="govuk-caption-l">Product schedule 1</span>You have added 2 products
              </h1>
            """,
            html,
        )

        # Check list_with_actions_kwargs
        assert response.context["list_with_actions_kwargs"] == {
            "rows": [
                {
                    "name": "<strong>Test product 1</strong>",
                    "actions": [
                        {
                            "label": "Remove",
                            "url": reverse(
                                "ecil:export-cfs:schedule-product-remove",
                                kwargs={
                                    "application_pk": self.app.pk,
                                    "schedule_pk": self.schedule.pk,
                                    "product_pk": self.p1.pk,
                                },
                            ),
                        },
                        {
                            "label": "Change",
                            "url": reverse(
                                "ecil:export-cfs:schedule-product-edit",
                                kwargs={
                                    "application_pk": self.app.pk,
                                    "schedule_pk": self.schedule.pk,
                                    "product_pk": self.p1.pk,
                                },
                            ),
                        },
                    ],
                },
                {
                    "name": "<strong>Test product 2</strong><br>Test product end use<br>Raw material",
                    "actions": [
                        {
                            "label": "Remove",
                            "url": reverse(
                                "ecil:export-cfs:schedule-product-remove",
                                kwargs={
                                    "application_pk": self.app.pk,
                                    "schedule_pk": self.schedule.pk,
                                    "product_pk": self.p2.pk,
                                },
                            ),
                        },
                        {
                            "label": "Change",
                            "url": reverse(
                                "ecil:export-cfs:schedule-product-edit",
                                kwargs={
                                    "application_pk": self.app.pk,
                                    "schedule_pk": self.schedule.pk,
                                    "product_pk": self.p2.pk,
                                },
                            ),
                        },
                    ],
                },
            ]
        }

    def test_post(self):
        # Test error message
        form_data = {"add_another": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "add_another": ["Select yes or no"],
        }

        # Test post success (yes)
        form_data = {"add_another": YesNoChoices.yes}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == get_cfs_schedule_url(
            "ecil:export-cfs:schedule-product-add", self.app, self.schedule
        )

        # Test post success (no)
        form_data = {"add_another": YesNoChoices.no}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == get_cfs_schedule_url(
            "export:cfs-schedule-edit", self.app, self.schedule
        )


class TestCFSScheduleProductConfirmRemoveFormView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.schedule = prototype_cfs_app_in_progress.schedules.first()

        self.p1 = self.schedule.products.create(
            product_name="Test product 1",
        )
        self.p2 = self.schedule.products.create(
            product_name="Test product 2",
            is_raw_material=True,
            product_end_use="Test product end use",
        )

        self.client = prototype_export_client
        self.url = reverse(
            "ecil:export-cfs:schedule-product-remove",
            kwargs={
                "application_pk": self.app.pk,
                "schedule_pk": self.schedule.pk,
                "product_pk": self.p1.pk,
            },
        )

    def test_permission(self, exporter_two_client):
        response = exporter_two_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/gds_form.html")

        expected_url = get_cfs_schedule_url(
            "ecil:export-cfs:schedule-product-add-another", self.app, self.schedule
        )
        assert_back_link_url(response, expected_url)

        # Check custom header is present
        html = response.content.decode("utf-8")
        assertInHTML(
            f"""
              <h1 class="govuk-fieldset__heading">
                <span class="govuk-caption-l">Product schedule 1</span>Are you sure you want to remove {self.p1.product_name}?
              </h1>
            """,
            html,
        )

    def test_post(self):
        # Test error message
        form_data = {"are_you_sure": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "are_you_sure": ["Select yes or no"],
        }

        # Test post success (no)
        assert self.schedule.products.count() == 2
        form_data = {"are_you_sure": YesNoChoices.no}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == get_cfs_schedule_url(
            "ecil:export-cfs:schedule-product-add-another", self.app, self.schedule
        )
        assert self.schedule.products.count() == 2

        # Test post success (yes)
        form_data = {"are_you_sure": YesNoChoices.yes}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == get_cfs_schedule_url(
            "ecil:export-cfs:schedule-product-add-another", self.app, self.schedule
        )
        assert self.schedule.products.count() == 1

        # Test removing last product redirects to correct view.
        url = reverse(
            "ecil:export-cfs:schedule-product-remove",
            kwargs={
                "application_pk": self.app.pk,
                "schedule_pk": self.schedule.pk,
                "product_pk": self.p2.pk,
            },
        )
        form_data = {"are_you_sure": YesNoChoices.yes}
        response = self.client.post(url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == get_cfs_schedule_url(
            "ecil:export-cfs:schedule-product-add", self.app, self.schedule
        )
        assert self.schedule.products.count() == 0
