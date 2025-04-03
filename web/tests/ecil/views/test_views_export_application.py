from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertTemplateUsed

from web.models import Country
from web.models.shared import YesNoChoices


class TestAnotherExportApplicationContactTemplateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_client, prototype_user):
        self.user = prototype_user
        self.url = reverse("ecil:export-application:another-contact")
        self.client = prototype_client

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_post_forbidden(self):
        response = self.client.post(self.url)

        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_get(self, exporter_site, prototype_cfs_app_in_progress):
        referer_url = reverse(
            "ecil:export-cfs:application-contact", kwargs={"application_pk": exporter_site.pk}
        )
        headers = {"REFERER": f"http://{exporter_site.domain}{referer_url}"}
        response = self.client.get(self.url, headers=headers)

        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/export_application/another_contact.html")

        assert response.context["back_link_kwargs"] == {"text": "Back", "href": referer_url}


class TestExportApplicationExportCountriesUpdateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_client, prototype_user, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.user = prototype_user
        self.url = reverse(
            "ecil:export-application:countries", kwargs={"application_pk": self.app.pk}
        )
        self.client = prototype_client

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/export_application/export_countries.html")

    def test_post(self):
        # Test error message
        form_data = {"countries": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "countries": ["Select a country or territory you want to export to"],
        }

        # Test post success
        valid_country = Country.app.get_cfs_countries().first()
        form_data = {"countries": valid_country.pk}
        response = self.client.post(self.url, data=form_data, follow=True)

        assert response.status_code == HTTPStatus.OK
        self.app.refresh_from_db()

        # Check extra context set now we've added a country
        context = response.context
        assert context["next_url"] == reverse(
            "ecil:export-cfs:schedule-create", kwargs={"application_pk": self.app.pk}
        )
        assert context["export_countries"]

        assert context["govuk_table_kwargs"] == {
            "caption": "You have added 1 country or territory",
            "captionClasses": "govuk-table__caption--m",
            "firstCellIsHeader": False,
            "rows": [
                [
                    {"text": "Afghanistan"},
                    {
                        "classes": "govuk-!-text-align-right",
                        "html": (
                            f'<a href="/ecil/export-application/{self.app.pk}/export-countries/{valid_country.pk}/remove/"'
                            ' class="govuk-link govuk-link--no-visited-state">Remove</a>'
                        ),
                    },
                ]
            ],
        }

        assert self.app.countries.count() == 1
        assert self.app.countries.filter(pk=valid_country.pk).exists()


class TestExportApplicationConfirmRemoveCountryFormView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_client, prototype_user, prototype_cfs_app_in_progress):
        self.valid_country = Country.app.get_cfs_countries().first()
        self.app = prototype_cfs_app_in_progress
        self.user = prototype_user
        self.url = reverse(
            "ecil:export-application:countries-remove",
            kwargs={"application_pk": self.app.pk, "country_pk": self.valid_country.pk},
        )
        self.client = prototype_client
        self.app.countries.add(self.valid_country)

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/gds_form.html")
        assertInHTML(
            f"Are you sure you want to remove {self.valid_country.name}?",
            response.content.decode("utf-8"),
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

        assert self.app.countries.count() == 1

        # Test post success
        form_data = {"are_you_sure": YesNoChoices.yes}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse(
            "ecil:export-application:countries", kwargs={"application_pk": self.app.pk}
        )

        self.app.refresh_from_db()
        assert self.app.countries.count() == 0
