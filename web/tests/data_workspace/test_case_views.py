from typing import Any

import pytest
from django.urls import reverse

from ._base import DT_STR_FORMAT, BaseTestDataView


class TestCaseDocumentDataView(BaseTestDataView):
    @pytest.fixture(autouse=True)
    def _setup(self, cw_client, completed_gmp_app, cfs_app_pre_sign, completed_com_app):
        self.client = cw_client
        self.url = reverse("data-workspace:case-document-data", kwargs={"version": "v0"})
        self.gmp = completed_gmp_app
        self.gmp.refresh_from_db
        self.gmp_cert = self.gmp.certificates.first()
        self.com = completed_com_app
        self.com_cert = self.com.certificates.first()
        self.cfs = cfs_app_pre_sign
        self.cfs_cert = self.cfs.certificates.first()

    def check_result(self, result: list[dict[str, Any]]) -> None:
        assert result["next"] == ""
        assert len(result["results"]) == 4
        assert result["results"] == [
            {
                "id": self.gmp_cert.document_references.first().pk,
                "application_id": self.gmp.pk,
                "document_pack_id": self.gmp_cert.pk,
                "document_pack_status": "AC",
                "issue_date": self.gmp_cert.case_completion_datetime.strftime(DT_STR_FORMAT),
                "country": "China",
                "document_type": "CERTIFICATE",
                "issue_paper_licence_only": None,
                "licence_end_date": None,
                "licence_start_date": None,
                "reference": "GMP/2025/00001",
            },
            {
                "id": self.cfs_cert.document_references.first().pk,
                "application_id": self.cfs.pk,
                "document_pack_id": self.cfs_cert.pk,
                "country": "Afghanistan",
                "document_type": "CERTIFICATE",
                "issue_date": None,
                "issue_paper_licence_only": None,
                "licence_end_date": None,
                "licence_start_date": None,
                "reference": "CFS/2025/00001",
                "document_pack_status": "DR",
            },
            {
                "id": self.cfs_cert.document_references.last().pk,
                "application_id": self.cfs.pk,
                "document_pack_id": self.cfs_cert.pk,
                "country": "Zimbabwe",
                "document_type": "CERTIFICATE",
                "issue_date": None,
                "issue_paper_licence_only": None,
                "licence_end_date": None,
                "licence_start_date": None,
                "reference": "CFS/2025/00002",
                "document_pack_status": "DR",
            },
            {
                "id": self.com_cert.document_references.first().pk,
                "application_id": self.com.pk,
                "document_pack_id": self.com_cert.pk,
                "country": "Afghanistan",
                "document_type": "CERTIFICATE",
                "issue_date": self.com_cert.case_completion_datetime.strftime(DT_STR_FORMAT),
                "issue_paper_licence_only": None,
                "licence_end_date": None,
                "licence_start_date": None,
                "reference": "COM/2025/00001",
                "document_pack_status": "AC",
            },
        ]
