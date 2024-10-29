from http import HTTPStatus

import pytest
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from pytest_django.asserts import assertContains, assertRedirects

from web.models import (
    CommodityGroup,
    CommodityType,
    Country,
    ImportApplicationType,
    Usage,
)
from web.tests.auth import AuthTestCase
from web.tests.conftest import LOGIN_URL

from .factory import CommodityFactory, CommodityGroupFactory


class TestCommodityListView(AuthTestCase):
    url = "/commodity/"
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_page_title(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.context_data["page_title"] == "Maintain Commodities"

    def test_number_of_pages(self):
        response = self.ilb_admin_client.get(self.url, {"commodity_code": ""})
        page = response.context_data["page"]

        # Page count has reduced as it is filter excluded commodity codes.
        assert page.paginator.num_pages == 62

    def test_page_results(self):
        response = self.ilb_admin_client.get(self.url, {"page": "2", "commodity_code": ""})
        page = response.context_data["page"]

        assert len(page.object_list) == 50


class TestCommodityCreateView(AuthTestCase):
    url = "/commodity/new/"
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_page_title(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.context_data["page_title"] == "New Commodity"


class TestCommodityUpdateView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.commodity = CommodityFactory(
            commodity_type=CommodityType.objects.first()
        )  # Create a commodity
        self.url = f"/commodity/{self.commodity.id}/edit/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_page_title(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.context["page_title"] == f"Editing {self.commodity}"


class TestCommodityDetailView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.commodity = CommodityFactory.create(commodity_type=CommodityType.objects.first())
        self.url = f"/commodity/{self.commodity.pk}/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_page_title(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.context["page_title"] == f"Viewing {self.commodity}"


class TestCommodityGroupCreateView(AuthTestCase):
    url = "/commodity/group/new/"
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_page_title(self):
        response = self.ilb_admin_client.get(self.url)
        assertContains(response, "Create Commodity Group")


class TestCommodityGroupUpdateView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.commodity_group = CommodityGroup.objects.first()
        self.url = f"/commodity/group/{self.commodity_group.id}/edit/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_page_title(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.context["page_title"] == f"Editing {self.commodity_group}"


class TestCommodityGroupDetailView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.commodity_group = CommodityGroup.objects.first()
        self.url = f"/commodity/group/{self.commodity_group.id}/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_page_title(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.context["page_title"] == f"Viewing {self.commodity_group}"


class TestCommodityUsage(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.commodity_group = CommodityGroupFactory()
        self.country = Country.objects.get(pk=131)
        self.application_type = ImportApplicationType.objects.get(
            type=ImportApplicationType.Types.FIREARMS, sub_type=ImportApplicationType.SubTypes.DFL
        )

    @freeze_time("2024-01-01")
    def test_add_usage_view_errors(self, ilb_admin_client):
        url = reverse("commodity-group-usage", kwargs={"pk": self.commodity_group.pk})
        resp = ilb_admin_client.get(url)
        assert resp.status_code == HTTPStatus.OK
        post_data = {
            "application_type": self.application_type.pk,
            "country": self.country.pk,
            "start_date": "03-Nov-2023",
            "end_date": "03-Jan-2021",
        }
        resp = ilb_admin_client.post(url, data=post_data)
        assert resp.context["form"].errors == {
            "end_date": [
                "End date must be after the start date",
                "End date must be today or in the future",
            ]
        }

    @freeze_time("2024-01-01")
    def test_add_usage_view_errors_today(self, ilb_admin_client):
        url = reverse("commodity-group-usage", kwargs={"pk": self.commodity_group.pk})
        resp = ilb_admin_client.get(url)
        assert resp.status_code == HTTPStatus.OK
        post_data = {
            "application_type": self.application_type.pk,
            "country": self.country.pk,
            "start_date": "03-Nov-2024",
            "end_date": "01-Jan-2024",
        }
        resp = ilb_admin_client.post(url, data=post_data)
        assert resp.context["form"].errors == {
            "end_date": ["End date must be after the start date"]
        }

    def test_add_usage_view(self, ilb_admin_client):
        url = reverse("commodity-group-usage", kwargs={"pk": self.commodity_group.pk})
        resp = ilb_admin_client.get(url)
        assert resp.status_code == HTTPStatus.OK

        resp = ilb_admin_client.post(url)
        assert resp.context["form"].errors == {
            "application_type": ["You must enter this item"],
            "country": ["You must enter this item"],
            "start_date": ["You must enter this item"],
        }

        resp = ilb_admin_client.post(
            url,
            data={
                "application_type": self.application_type.pk,
                "country": self.country.pk,
                "start_date": "03-Nov-2023",
            },
        )
        usage = Usage.objects.get(
            country=self.country,
            application_type=self.application_type,
            commodity_group=self.commodity_group,
        )

        assertRedirects(
            resp,
            reverse(
                "commodity-group-usage-edit",
                kwargs={"commodity_group_pk": self.commodity_group.pk, "usage_pk": usage.pk},
            ),
        )

    def test_edit_usage_view(self, ilb_admin_client):
        usage = Usage.objects.create(
            country=self.country,
            application_type=self.application_type,
            commodity_group=self.commodity_group,
            start_date=timezone.now().today(),
        )
        url = reverse(
            "commodity-group-usage-edit",
            kwargs={"commodity_group_pk": self.commodity_group.pk, "usage_pk": usage.pk},
        )
        resp = ilb_admin_client.get(url)
        assert resp.status_code == HTTPStatus.OK
        new_country = Country.objects.get(pk=39)

        resp = ilb_admin_client.post(
            url,
            data={
                "application_type": self.application_type.pk,
                "country": new_country.pk,
                "start_date": "03-Jan-2022",
            },
        )
        assertRedirects(
            resp,
            reverse(
                "commodity-group-usage-edit",
                kwargs={"commodity_group_pk": self.commodity_group.pk, "usage_pk": usage.pk},
            ),
        )
        usage.refresh_from_db()
        assert usage.country == new_country

    def test_delete_usage_view(self, ilb_admin_client):
        usage = Usage.objects.create(
            country=self.country,
            application_type=self.application_type,
            commodity_group=self.commodity_group,
            start_date=timezone.now().today(),
        )
        assert Usage.objects.filter(commodity_group=self.commodity_group).count() == 1
        url = reverse(
            "commodity-group-usage-delete",
            kwargs={"commodity_group_pk": self.commodity_group.pk, "usage_pk": usage.pk},
        )
        resp = ilb_admin_client.post(url)
        assertRedirects(
            resp,
            reverse(
                "commodity-group-edit",
                kwargs={"pk": self.commodity_group.pk},
            ),
            HTTPStatus.FOUND,
        )
        assert Usage.objects.filter(commodity_group=self.commodity_group).count() == 0
