from unittest import mock

import pytest
from django.test import override_settings
from django.utils import timezone

from web.domains.case.shared import ImpExpStatus
from web.domains.chief import client
from web.domains.chief.types import CreateLicenceData
from web.models import ImportApplicationLicence, LiteHMRCChiefRequest, Task


@pytest.fixture(autouse=True)
def send_to_chief_enabled():
    """Ensure SEND_LICENCE_TO_CHIEF is set to true for all tests"""
    with override_settings(SEND_LICENCE_TO_CHIEF=True):
        yield None


class TestChiefClient:
    def test_request_license(self, requests_mock):
        example_domain = "http://example.com/"
        chief_url = "update"
        url = f"{example_domain}{chief_url}"

        mock_response_headers = {
            "Content-Type": "text/plain",
            "Server-Authorization": 'Hawk mac="fake-mac", hash="fake-hash"',
        }
        requests_mock.post(url, headers=mock_response_headers, text="OK")
        # Finished mocking the API response.

        data = mock.create_autospec(spec=CreateLicenceData, instance=True)
        data.json.return_value = '{"foo": "bar"}'

        with mock.patch("mohawk.sender.Sender.accept_response"):
            with override_settings(
                ICMS_HMRC_DOMAIN=example_domain, ICMS_HMRC_UPDATE_LICENCE_ENDPOINT=chief_url
            ):
                response = client.request_license(data)

        assert response.status_code == 200
        assert response.content == b"OK"
        assert response.headers["Content-type"] == "text/plain"

    def test_send_application_to_chief(self, fa_sil_app_doc_signing, monkeypatch):
        # Setup
        app = fa_sil_app_doc_signing
        licence = app.licences.get(status=ImportApplicationLicence.Status.DRAFT)

        current_task = app.get_expected_task(
            Task.TaskType.DOCUMENT_SIGNING, select_for_update=False
        )

        request_license_mock = mock.create_autospec(spec=client.request_license)
        monkeypatch.setattr(client, "request_license", request_license_mock)

        # Test
        client.send_application_to_chief(app, current_task)

        # Asserts
        request_license_mock.assert_called_once()
        app.refresh_from_db()
        assert app.chief_references.count() == 1

        chief_req: LiteHMRCChiefRequest = app.chief_references.first()

        assert chief_req.case_reference == app.reference
        assert chief_req.request_data == {
            "licence": {
                "action": "insert",
                "reference": "IMI/2022/12345",
                "licence_reference": "dummy-reference",
                "country_code": "DE",
                "country_group": None,
                "end_date": "2023-12-01",
                "goods": [],
                "id": str(chief_req.lite_hmrc_id),
                "organisation": {
                    "address": {
                        "line_1": "47 some way",
                        "line_2": "someplace",
                        "line_3": "",
                        "line_4": "",
                        "line_5": "",
                        "postcode": "BT180LZ",  # /PS-IGNORE
                    },
                    "end_date": None,
                    "eori_number": "GB0123456789ABCDE",
                    "name": "UK based importer",
                    "start_date": None,
                },
                "restrictions": "",
                "start_date": licence.licence_start_date.strftime("%Y-%m-%d"),
                "type": "SIL",
            }
        }

        app.get_expected_task(Task.TaskType.CHIEF_WAIT, select_for_update=False)

    def test_send_application_to_chief_errors(self, fa_sil_app_doc_signing, monkeypatch):
        # Setup
        app = fa_sil_app_doc_signing
        current_task = app.get_expected_task(
            Task.TaskType.DOCUMENT_SIGNING, select_for_update=False
        )

        # make request_licence fail after the LiteHMRCChiefRequest object is created
        request_license_mock = mock.create_autospec(
            spec=client.request_license,
            side_effect=RuntimeError("Something unexpected has happened..."),
        )
        monkeypatch.setattr(client, "request_license", request_license_mock)

        # Test
        client.send_application_to_chief(app, current_task)

        # Asserts
        app.refresh_from_db()
        app.get_expected_task(Task.TaskType.CHIEF_ERROR, select_for_update=False)

        assert app.chief_references.count() == 1
        assert (
            app.chief_references.first().status == LiteHMRCChiefRequest.CHIEFStatus.INTERNAL_ERROR
        )

    def test_send_application_to_chief_variation_request(self, fa_sil_app_doc_signing, monkeypatch):
        # Setup
        app = fa_sil_app_doc_signing
        licence = app.licences.get(status=ImportApplicationLicence.Status.DRAFT)

        current_task = app.get_expected_task(
            Task.TaskType.DOCUMENT_SIGNING, select_for_update=False
        )

        request_license_mock = mock.create_autospec(spec=client.request_license)
        monkeypatch.setattr(client, "request_license", request_license_mock)

        # Create a fake LiteHMRCChiefRequest (for the previous payload)
        LiteHMRCChiefRequest.objects.create(
            import_application=app,
            case_reference=app.reference,
            request_data={"foo": "bar", "test": "data"},
            request_sent_datetime=timezone.now(),
        )
        # Fake a variation request
        app.reference = f"{app.reference}/1"
        app.status = ImpExpStatus.VARIATION_REQUESTED
        app.save()

        # Test
        client.send_application_to_chief(app, current_task)

        # Asserts
        request_license_mock.assert_called_once()
        app.refresh_from_db()
        assert app.chief_references.count() == 2

        chief_req: LiteHMRCChiefRequest = app.chief_references.latest("request_sent_datetime")

        assert chief_req.case_reference == app.reference
        assert chief_req.request_data == {
            "licence": {
                "action": "replace",
                "reference": "IMI/2022/12345/1",
                "licence_reference": "dummy-reference",
                "country_code": "DE",
                "country_group": None,
                "end_date": "2023-12-01",
                "goods": [],
                "id": str(chief_req.lite_hmrc_id),
                "organisation": {
                    "address": {
                        "line_1": "47 some way",
                        "line_2": "someplace",
                        "line_3": "",
                        "line_4": "",
                        "line_5": "",
                        "postcode": "BT180LZ",  # /PS-IGNORE
                    },
                    "end_date": None,
                    "eori_number": "GB0123456789ABCDE",
                    "name": "UK based importer",
                    "start_date": None,
                },
                "restrictions": "",
                "start_date": licence.licence_start_date.strftime("%Y-%m-%d"),
                "type": "SIL",
            }
        }

        app.get_expected_task(Task.TaskType.CHIEF_WAIT, select_for_update=False)
