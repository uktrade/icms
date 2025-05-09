from typing import Any

import pytest
from django.urls import reverse

from ._base import BaseTestDataView


class TestExportApplicationDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client, cfs_app_processing, completed_gmp_app, com_app_submitted):
        self.client = cw_client
        self.url = reverse("data-workspace:export-application-data", kwargs={"version": "v0"})

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        apps = result["results"]
        assert len(apps) == 3


class TestGMPApplicationDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client, completed_gmp_app):
        self.client = cw_client
        self.url = reverse("data-workspace:gmp-application-data", kwargs={"version": "v0"})

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        apps = result["results"]
        assert len(apps) == 1


class TestCOMApplicationDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client, com_app_submitted, com_agent_app_submitted):
        self.client = cw_client
        self.url = reverse("data-workspace:com-application-data", kwargs={"version": "v0"})

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        apps = result["results"]
        assert len(apps) == 2


class TestCFSSchedulenDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client, cfs_app_processing):
        self.client = cw_client
        self.url = reverse("data-workspace:cfs-schedule-data", kwargs={"version": "v0"})

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        schedules = result["results"]
        assert len(schedules) == 1


class TestCFSProductDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client, cfs_app_processing):
        self.client = cw_client
        self.url = reverse("data-workspace:cfs-product-data", kwargs={"version": "v0"})

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        products = result["results"]
        assert len(products) == 1
