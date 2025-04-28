from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertTemplateUsed

from web.ecil.gds.forms import fields
from web.models import CFSSchedule, Country, ProductLegislation
from web.models.shared import AddressEntryType, YesNoChoices


class TestCFSApplicationReferenceUpdateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_export_user, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.url = reverse(
            "ecil:export-cfs:application-reference", kwargs={"application_pk": self.app.pk}
        )
        self.client = prototype_export_client

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
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
        assert response.url == reverse(
            "ecil:export-cfs:application-contact", kwargs={"application_pk": self.app.pk}
        )

        # Test post success
        form_data = {"applicant_reference": "test-application-reference"}
        response = self.client.post(self.url, data=form_data)

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse(
            "ecil:export-cfs:application-contact", kwargs={"application_pk": self.app.pk}
        )

        self.app.refresh_from_db()
        assert self.app.applicant_reference == "test-application-reference"


class TestCFSApplicationContactUpdateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_export_user, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.user = prototype_export_user
        self.url = reverse(
            "ecil:export-cfs:application-contact", kwargs={"application_pk": self.app.pk}
        )
        self.client = prototype_export_client

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/gds_form.html")

        assert response.context["back_link_kwargs"] == {
            "text": "Back",
            "href": reverse(
                "ecil:export-cfs:application-reference", kwargs={"application_pk": self.app.pk}
            ),
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
        assert response.url == reverse(
            "ecil:export-application:countries", kwargs={"application_pk": self.app.pk}
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
        self.url = reverse(
            "ecil:export-cfs:schedule-create", kwargs={"application_pk": self.app.pk}
        )
        self.client = prototype_export_client

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/cfs/schedule_create.html")

        assert response.context["back_link_kwargs"] == {
            "text": "Back",
            "href": reverse(
                "ecil:export-application:countries", kwargs={"application_pk": self.app.pk}
            ),
        }

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
        assert response.url == reverse(
            "ecil:export-cfs:schedule-exporter-status",
            kwargs={"application_pk": self.app.pk, "schedule_pk": self.app.schedules.last().pk},
        )


class TestCFSScheduleExporterStatusUpdateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.schedule = prototype_cfs_app_in_progress.schedules.first()
        self.url = reverse(
            "ecil:export-cfs:schedule-exporter-status",
            kwargs={"application_pk": self.app.pk, "schedule_pk": self.schedule.pk},
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

        assert response.context["back_link_kwargs"]["href"] == reverse(
            "ecil:export-cfs:schedule-create", kwargs={"application_pk": self.app.pk}
        )

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
        assert response.url == reverse(
            "ecil:export-cfs:schedule-manufacturer-address",
            kwargs={"application_pk": self.app.pk, "schedule_pk": self.schedule.pk},
        )

        self.schedule.refresh_from_db()
        assert self.schedule.exporter_status == CFSSchedule.ExporterStatus.IS_MANUFACTURER


class TestCFSScheduleManufacturerAddressUpdateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.schedule = prototype_cfs_app_in_progress.schedules.first()
        self.url = reverse(
            "ecil:export-cfs:schedule-manufacturer-address",
            kwargs={"application_pk": self.app.pk, "schedule_pk": self.schedule.pk},
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

        assert response.context["back_link_kwargs"]["href"] == reverse(
            "ecil:export-cfs:schedule-exporter-status",
            kwargs={"application_pk": self.app.pk, "schedule_pk": self.schedule.pk},
        )

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
        assert response.url == reverse(
            "ecil:export-cfs:schedule-brand-name-holder",
            kwargs={"application_pk": self.app.pk, "schedule_pk": self.schedule.pk},
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
        self.url = reverse(
            "ecil:export-cfs:schedule-brand-name-holder",
            kwargs={"application_pk": self.app.pk, "schedule_pk": self.schedule.pk},
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

        assert response.context["back_link_kwargs"]["href"] == reverse(
            "ecil:export-cfs:schedule-manufacturer-address",
            kwargs={"application_pk": self.app.pk, "schedule_pk": self.schedule.pk},
        )

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
        assert response.url == reverse(
            "ecil:export-cfs:schedule-country-of-manufacture",
            kwargs={"application_pk": self.app.pk, "schedule_pk": self.schedule.pk},
        )

        self.schedule.refresh_from_db()
        assert self.schedule.brand_name_holder == YesNoChoices.yes


class TestCFSScheduleCountryOfManufactureUpdateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.schedule = prototype_cfs_app_in_progress.schedules.first()
        self.url = reverse(
            "ecil:export-cfs:schedule-country-of-manufacture",
            kwargs={"application_pk": self.app.pk, "schedule_pk": self.schedule.pk},
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

        assert response.context["back_link_kwargs"]["href"] == reverse(
            "ecil:export-cfs:schedule-brand-name-holder",
            kwargs={"application_pk": self.app.pk, "schedule_pk": self.schedule.pk},
        )

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
        assert response.url == reverse(
            "ecil:export-cfs:schedule-legislation",
            kwargs={"application_pk": self.app.pk, "schedule_pk": self.schedule.pk},
        )

        self.schedule.refresh_from_db()
        assert self.schedule.country_of_manufacture == valid_country


class TestCFSScheduleAddLegislationUpdateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.schedule = prototype_cfs_app_in_progress.schedules.first()
        self.url = reverse(
            "ecil:export-cfs:schedule-legislation",
            kwargs={"application_pk": self.app.pk, "schedule_pk": self.schedule.pk},
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

        assert response.context["back_link_kwargs"]["href"] == reverse(
            "ecil:export-cfs:schedule-country-of-manufacture",
            kwargs={"application_pk": self.app.pk, "schedule_pk": self.schedule.pk},
        )

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
        referrer = reverse(
            "ecil:export-cfs:schedule-legislation-add-another",
            kwargs={"application_pk": self.app.pk, "schedule_pk": self.schedule.pk},
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
        assert response.url == reverse(
            "ecil:export-cfs:schedule-legislation-add-another",
            kwargs={"application_pk": self.app.pk, "schedule_pk": self.schedule.pk},
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

        self.url = reverse(
            "ecil:export-cfs:schedule-legislation-add-another",
            kwargs={"application_pk": self.app.pk, "schedule_pk": self.schedule.pk},
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
        assertTemplateUsed(response, "ecil/cfs/schedule_legislation_add_another.html")

        assert response.context["back_link_kwargs"]["href"] == reverse(
            "ecil:export-cfs:schedule-legislation",
            kwargs={"application_pk": self.app.pk, "schedule_pk": self.schedule.pk},
        )

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
        assert response.url == reverse(
            "ecil:export-cfs:schedule-legislation",
            kwargs={"application_pk": self.app.pk, "schedule_pk": self.schedule.pk},
        )

        # Test post success (no)
        form_data = {"add_another": YesNoChoices.no}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse(
            "export:cfs-schedule-edit",
            kwargs={"application_pk": self.app.pk, "schedule_pk": self.schedule.pk},
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

    def test_get(self, exporter_site):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/gds_form.html")

        assert response.context["back_link_kwargs"]["href"] == reverse(
            "ecil:export-cfs:schedule-legislation-add-another",
            kwargs={"application_pk": self.app.pk, "schedule_pk": self.schedule.pk},
        )

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
        assert response.url == reverse(
            "ecil:export-cfs:schedule-legislation-add-another",
            kwargs={"application_pk": self.app.pk, "schedule_pk": self.schedule.pk},
        )
        assert self.schedule.legislations.count() == 2

        # Test post success (yes)
        form_data = {"are_you_sure": YesNoChoices.yes}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse(
            "ecil:export-cfs:schedule-legislation-add-another",
            kwargs={"application_pk": self.app.pk, "schedule_pk": self.schedule.pk},
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
        assert response.url == reverse(
            "ecil:export-cfs:schedule-legislation",
            kwargs={"application_pk": self.app.pk, "schedule_pk": self.schedule.pk},
        )
        assert self.schedule.legislations.count() == 0
