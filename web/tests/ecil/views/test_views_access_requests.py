from http import HTTPStatus

import pytest
from django.urls import reverse
from pydantic import ValidationError

from web.models import Country, ExporterAccessRequest
from web.models.shared import YesNoChoices


class TestExporterAccessRequestTypeFormView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_client, prototype_user):
        self.user = prototype_user
        self.url = reverse("ecil:access_request:new")
        self.client = prototype_client

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_exporter_redirect(self):
        form_data = {"request_type": ExporterAccessRequest.MAIN_EXPORTER_ACCESS}
        response = self.client.post(self.url, data=form_data)

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse(
            "ecil:access_request:exporter_step_form", kwargs={"step": "company-details"}
        )

    def test_agent_redirect(self):
        form_data = {"request_type": ExporterAccessRequest.AGENT_ACCESS}
        response = self.client.post(self.url, data=form_data)

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse(
            "ecil:access_request:exporter_agent_step_form", kwargs={"step": "agent-company-details"}
        )


class TestExporterAccessRequestMultiStepFormView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_client, prototype_user):
        self.user = prototype_user
        self.client = prototype_client

    def get_url(self, step: str) -> str:
        return reverse("ecil:access_request:exporter_step_form", kwargs={"step": step})

    def test_permission(self, ilb_admin_client):
        url = self.get_url(step="company-details")

        response = ilb_admin_client.get(url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_exporter_access_request(self):
        #
        # Company details
        form_data = {
            "organisation_name": "test organisation name",
            "organisation_trading_name": "test organisation trading name",
            "organisation_registered_number": "test organisation registered name",
            "organisation_address": "test organisation address",
        }
        response = self.client.post(self.get_url(step="company-details"), data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == self.get_url("company-purpose")

        #
        # Company purpose
        form_data = {
            "organisation_purpose": "test organisation purpose",
        }
        response = self.client.post(self.get_url(step="company-purpose"), data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == self.get_url("company-products")

        #
        # Company products
        form_data = {
            "organisation_products": "test organisation products",
        }
        response = self.client.post(self.get_url(step="company-products"), data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == self.get_url("export-countries")

        #
        # Export countries
        uk = Country.objects.get(name="United Kingdom")
        germany = Country.objects.get(name="Germany")
        france = Country.objects.get(name="France")

        for c in [uk, germany, france]:
            form_data = {"export_countries": c.pk}
            response = self.client.post(self.get_url(step="export-countries"), data=form_data)
            assert response.status_code == HTTPStatus.FOUND
            assert response.url == self.get_url("export-countries")

        #
        # Check summary URL is located in export-countries step
        response = self.client.get(self.get_url(step="export-countries"))
        assert response.status_code == HTTPStatus.OK
        assert response.context["summary_url"] == reverse(
            "ecil:access_request:exporter_step_form_summary"
        )

        #
        # Check submitting all the session data creates an access request.
        response = self.client.post(response.context["summary_url"])
        assert response.status_code == HTTPStatus.FOUND

        access_request = ExporterAccessRequest.objects.last()
        assert response.url == reverse(
            "ecil:access_request:submitted_detail", kwargs={"access_request_pk": access_request.pk}
        )

        assert access_request.organisation_name == "test organisation name"
        assert access_request.organisation_trading_name == "test organisation trading name"
        assert access_request.organisation_registered_number == "test organisation registered name"
        assert access_request.organisation_address == "test organisation address"
        assert access_request.organisation_purpose == "test organisation purpose"
        assert access_request.organisation_products == "test organisation products"

        assert access_request.export_countries.all().count() == 3
        for c in [uk, germany, france]:
            assert access_request.export_countries.contains(c)


class TestExporterAccessRequestAgentMultiStepFormView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_client, prototype_user):
        self.user = prototype_user
        self.client = prototype_client

    def get_url(self, step: str) -> str:
        return reverse("ecil:access_request:exporter_agent_step_form", kwargs={"step": step})

    def test_permission(self, ilb_admin_client):
        url = self.get_url(step="agent-company-details")

        response = ilb_admin_client.get(url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_exporter_access_request(self):
        #
        # Agent Company details
        form_data = {
            "agent_name": "test agent name",
            "agent_trading_name": "test agent trading name",
            "agent_address": "test agent address",
        }
        response = self.client.post(self.get_url(step="agent-company-details"), data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == self.get_url("company-details")

        #
        # Company details
        form_data = {
            "organisation_name": "test organisation name",
            "organisation_trading_name": "test organisation trading name",
            "organisation_registered_number": "test organisation registered name",
            "organisation_address": "test organisation address",
        }
        response = self.client.post(self.get_url(step="company-details"), data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == self.get_url("company-purpose")

        #
        # Company purpose
        form_data = {
            "organisation_purpose": "test organisation purpose",
        }
        response = self.client.post(self.get_url(step="company-purpose"), data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == self.get_url("company-products")

        #
        # Company products
        form_data = {
            "organisation_products": "test organisation products",
        }
        response = self.client.post(self.get_url(step="company-products"), data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == self.get_url("export-countries")

        #
        # Export countries
        uk = Country.objects.get(name="United Kingdom")
        germany = Country.objects.get(name="Germany")
        france = Country.objects.get(name="France")

        for c in [uk, germany, france]:
            form_data = {"export_countries": c.pk}
            response = self.client.post(self.get_url(step="export-countries"), data=form_data)
            assert response.status_code == HTTPStatus.FOUND
            assert response.url == self.get_url("export-countries")

        #
        # Check summary URL is located in export-countries step
        response = self.client.get(self.get_url(step="export-countries"))
        assert response.status_code == HTTPStatus.OK
        assert response.context["summary_url"] == reverse(
            "ecil:access_request:exporter_agent_step_form_summary"
        )

        #
        # Check submitting all the session data creates an access request.
        response = self.client.post(response.context["summary_url"])
        assert response.status_code == HTTPStatus.FOUND

        access_request = ExporterAccessRequest.objects.last()
        assert response.url == reverse(
            "ecil:access_request:submitted_detail", kwargs={"access_request_pk": access_request.pk}
        )

        assert access_request.agent_name == "test agent name"
        assert access_request.agent_trading_name == "test agent trading name"
        assert access_request.agent_address == "test agent address"
        assert access_request.organisation_name == "test organisation name"
        assert access_request.organisation_trading_name == "test organisation trading name"
        assert access_request.organisation_registered_number == "test organisation registered name"
        assert access_request.organisation_address == "test organisation address"
        assert access_request.organisation_purpose == "test organisation purpose"
        assert access_request.organisation_products == "test organisation products"

        assert access_request.export_countries.all().count() == 3
        for c in [uk, germany, france]:
            assert access_request.export_countries.contains(c)


class TestExporterAccessRequestMultiStepFormSummaryView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_client):
        self.client = prototype_client
        self.url = reverse("ecil:access_request:exporter_step_form_summary")

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        # TODO: Revisit in ECIL-618
        #       Summary screen will not render partially valid data with Pydantic
        with pytest.raises(ValidationError):
            self.client.get(self.url)

    # happy path has been tested above in TestExporterAccessRequestMultiStepFormView.
    def test_post_errors(self):
        with pytest.raises(ValidationError):
            self.client.post(self.url)

            # TODO: Revisit in ECIL-618
            #       Decide if we want to support partially valid summary views.


class TestExporterAccessRequestAgentMultiStepFormSummaryView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_client):
        self.client = prototype_client
        self.url = reverse("ecil:access_request:exporter_step_form_summary")

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        # TODO: Revisit in ECIL-618
        #       Summary screen will not render partially valid data with Pydantic
        with pytest.raises(ValidationError):
            self.client.get(self.url)

    # happy path has been tested above in TestExporterAccessRequestAgentMultiStepFormView.
    def test_post_errors(self):
        with pytest.raises(ValidationError):
            self.client.post(self.url)

            # TODO: Revisit in ECIL-618
            #       Decide if we want to support partially valid summary views.


class TestExporterAccessRequestConfirmRemoveCountryFormView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_client, prototype_user):
        self.user = prototype_user
        self.client = prototype_client

        self.exporter_country_url = reverse(
            "ecil:access_request:exporter_step_form", kwargs={"step": "export-countries"}
        )
        self.exporter_agent_country_url = reverse(
            "ecil:access_request:exporter_agent_step_form", kwargs={"step": "export-countries"}
        )

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.exporter_country_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.exporter_country_url)
        assert response.status_code == HTTPStatus.OK

        response = ilb_admin_client.get(self.exporter_agent_country_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.exporter_agent_country_url)
        assert response.status_code == HTTPStatus.OK

    def test_exporter_remove_country(self):
        # add a country
        uk = Country.objects.get(name="United Kingdom")
        form_data = {"export_countries": uk.pk}
        self.client.post(self.exporter_country_url, data=form_data)

        session_key = "ExporterAccessRequestMultiStepFormView-export-countries-export_countries"
        assert self.client.session[session_key] == [str(uk.pk)]

        # remove a country
        url = reverse(
            "ecil:access_request:remove_export_country_form", kwargs={"country_pk": uk.pk}
        )
        form_data = {"are_you_sure": YesNoChoices.yes}
        response = self.client.post(url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == self.exporter_country_url

        assert self.client.session[session_key] == []

    def test_agent_remove_country(self, caseworker_site):
        # add a country
        uk = Country.objects.get(name="United Kingdom")
        form_data = {"export_countries": uk.pk}
        self.client.post(self.exporter_agent_country_url, data=form_data)

        session_key = (
            "ExporterAccessRequestAgentMultiStepFormView-export-countries-export_countries"
        )
        assert self.client.session[session_key] == [str(uk.pk)]

        # remove a country
        url = reverse(
            "ecil:access_request:remove_export_country_form", kwargs={"country_pk": uk.pk}
        )

        # get request to store the referrer header
        headers = {"REFERER": f"http://{caseworker_site.domain}{self.exporter_agent_country_url}"}
        response = self.client.get(url, headers=headers)
        assert response.status_code == HTTPStatus.OK

        # Now post to check country is removed and redirect url is correct.
        form_data = {"are_you_sure": YesNoChoices.yes}
        response = self.client.post(url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == self.exporter_agent_country_url

        assert self.client.session[session_key] == []


class TestAccessRequestSubmittedDetailView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_client, prototype_user, exporter_access_request):
        self.ear = exporter_access_request
        exporter_access_request.submitted_by = prototype_user
        exporter_access_request.save()

        self.url = reverse(
            "ecil:access_request:submitted_detail",
            kwargs={"access_request_pk": exporter_access_request.pk},
        )
        self.client = prototype_client

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_post_forbidden(self):
        response = self.client.post(self.url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        assert response.context["panel_kwargs"] == {
            "html": f"Your reference number is <strong>{self.ear.reference}</strong>",
            "titleText": "Access request submitted",
        }

    def test_404(self, exporter_one_contact):
        self.ear.submitted_by = exporter_one_contact
        self.ear.save()

        response = self.client.get(self.url)

        # You can only view your own access requests.
        assert response.status_code == HTTPStatus.NOT_FOUND
