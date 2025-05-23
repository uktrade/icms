import datetime as dt
from typing import Any

import pytest
from django.urls import reverse

from web.models import CaseNote, VariationRequest

from ._base import DT_STR_FORMAT, BaseTestDataView


class TestCaseNoteDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(
        self,
        cw_client,
        exporter_one_contact,
        com_app_submitted,
        importer_one_contact,
        fa_dfl_app_pre_sign,
    ):
        self.client = cw_client
        self.url = reverse("data-workspace:case-note-data", kwargs={"version": "v0"})
        self.com = com_app_submitted
        self.com_cn = CaseNote.objects.create(note="test note", created_by=exporter_one_contact)
        self.com.case_notes.add(self.com_cn)
        self.dfl = fa_dfl_app_pre_sign
        self.dfl_cn = CaseNote.objects.create(note="test note 2", created_by=importer_one_contact)
        self.dfl.case_notes.add(self.dfl_cn)

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["results"] == [
            {
                "application_id": self.com.pk,
                "id": self.com_cn.pk,
                "note": "test note",
                "file_count": 0,
                "create_datetime": self.com_cn.create_datetime.strftime(DT_STR_FORMAT),
                "created_by_id": self.com_cn.created_by_id,
                "updated_at": self.com_cn.updated_at.strftime(DT_STR_FORMAT),
                "updated_by_id": None,
            },
            {
                "application_id": self.dfl.pk,
                "id": self.dfl_cn.pk,
                "note": "test note 2",
                "file_count": 0,
                "create_datetime": self.dfl_cn.create_datetime.strftime(DT_STR_FORMAT),
                "created_by_id": self.dfl_cn.created_by_id,
                "updated_at": self.dfl_cn.updated_at.strftime(DT_STR_FORMAT),
                "updated_by_id": None,
            },
        ]


class TestVariationRequestDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(
        self,
        cw_client,
        exporter_one_contact,
        com_app_submitted,
        importer_one_contact,
        fa_dfl_app_pre_sign,
    ):
        self.client = cw_client
        self.url = reverse("data-workspace:variation-request-data", kwargs={"version": "v0"})
        self.com = com_app_submitted
        self.com_vr = VariationRequest.objects.create(
            status=VariationRequest.Statuses.OPEN,
            requested_by=exporter_one_contact,
            what_varied="test what",
        )
        self.com.variation_requests.add(self.com_vr)
        self.dfl = fa_dfl_app_pre_sign
        self.dfl_vr = VariationRequest.objects.create(
            status=VariationRequest.Statuses.ACCEPTED,
            requested_by=importer_one_contact,
            what_varied="test what",
            why_varied="test why",
            when_varied=dt.date(2025, 5, 23),
        )
        self.dfl.variation_requests.add(self.dfl_vr)

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["results"] == [
            {
                "application_id": self.com.pk,
                "closed_by_id": None,
                "closed_datetime": None,
                "extension_flag": False,
                "id": self.com_vr.pk,
                "reject_cancellation_reason": None,
                "requested_by_id": self.com_vr.requested_by_id,
                "requested_datetime": self.com_vr.requested_datetime.strftime(DT_STR_FORMAT),
                "status": "OPEN",
                "update_request_reason": None,
                "what_varied": "test what",
                "when_varied": None,
                "why_varied": None,
            },
            {
                "application_id": self.dfl.pk,
                "closed_by_id": None,
                "closed_datetime": None,
                "extension_flag": False,
                "id": self.dfl_vr.pk,
                "reject_cancellation_reason": None,
                "requested_by_id": self.dfl_vr.requested_by_id,
                "requested_datetime": self.dfl_vr.requested_datetime.strftime(DT_STR_FORMAT),
                "status": "ACCEPTED",
                "update_request_reason": None,
                "what_varied": "test what",
                "when_varied": "2025-05-23",
                "why_varied": "test why",
            },
        ]
