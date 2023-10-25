from unittest import mock

import pytest
from django.test import override_settings
from django.utils import timezone

from web.domains.case.services import case_progress, document_pack
from web.domains.case.shared import ImpExpStatus
from web.domains.chief import client
from web.domains.chief.types import LicenceDataPayload
from web.models import ICMSHMRCChiefRequest, ImportApplicationLicence, Task


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

        data = mock.create_autospec(spec=LicenceDataPayload, instance=True)
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

        current_task = case_progress.get_expected_task(app, Task.TaskType.DOCUMENT_SIGNING)

        request_license_mock = mock.create_autospec(spec=client.request_license)
        monkeypatch.setattr(client, "request_license", request_license_mock)

        # Test
        client.send_application_to_chief(app, current_task)

        # Asserts
        request_license_mock.assert_called_once()
        app.refresh_from_db()
        assert app.chief_references.count() == 1

        chief_req: ICMSHMRCChiefRequest = app.chief_references.first()

        assert chief_req.case_reference == app.reference
        assert chief_req.request_data == {
            "licence": {
                "action": "insert",
                "reference": "IMI/2022/12345",
                "licence_reference": "dummy-reference",
                "country_code": "DE",
                "country_group": None,
                "start_date": licence.licence_start_date.strftime("%Y-%m-%d"),
                "end_date": licence.licence_end_date.strftime("%Y-%m-%d"),
                "goods": [],
                "id": str(chief_req.icms_hmrc_id),
                "organisation": {
                    "address": {
                        "line_1": "I1 address line 1",
                        "line_2": "I1 address line 2",
                        "line_3": "",
                        "line_4": "",
                        "line_5": "",
                        "postcode": "BT180LZ",  # /PS-IGNORE
                    },
                    "end_date": None,
                    "eori_number": "GB0123456789ABCDE",
                    "name": "Test Importer 1",
                    "start_date": None,
                },
                "restrictions": "",
                "type": "SIL",
            }
        }

        case_progress.check_expected_task(app, Task.TaskType.CHIEF_WAIT)

    def test_send_application_to_chief_errors(self, fa_sil_app_doc_signing, monkeypatch):
        # Setup
        app = fa_sil_app_doc_signing
        current_task = case_progress.get_expected_task(app, Task.TaskType.DOCUMENT_SIGNING)

        # make request_licence fail after the ICMSHMRCChiefRequest object is created
        request_license_mock = mock.create_autospec(
            spec=client.request_license,
            side_effect=RuntimeError("Something unexpected has happened..."),
        )
        monkeypatch.setattr(client, "request_license", request_license_mock)

        # Test
        client.send_application_to_chief(app, current_task)

        # Asserts
        app.refresh_from_db()
        case_progress.check_expected_task(app, Task.TaskType.CHIEF_ERROR)

        assert app.chief_references.count() == 1
        assert (
            app.chief_references.first().status == ICMSHMRCChiefRequest.CHIEFStatus.INTERNAL_ERROR
        )

    def test_send_application_to_chief_variation_request(self, fa_sil_app_doc_signing, monkeypatch):
        # Setup
        app = fa_sil_app_doc_signing
        licence = app.licences.get(status=ImportApplicationLicence.Status.DRAFT)

        current_task = case_progress.get_expected_task(app, Task.TaskType.DOCUMENT_SIGNING)

        request_license_mock = mock.create_autospec(spec=client.request_license)
        monkeypatch.setattr(client, "request_license", request_license_mock)

        # Create a fake ICMSHMRCChiefRequest (for the previous payload)
        ICMSHMRCChiefRequest.objects.create(
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

        chief_req: ICMSHMRCChiefRequest = app.chief_references.latest("request_sent_datetime")

        assert chief_req.case_reference == app.reference
        assert chief_req.request_data == {
            "licence": {
                "action": "replace",
                "reference": "IMI/2022/12345/1",
                "licence_reference": "dummy-reference",
                "country_code": "DE",
                "country_group": None,
                "goods": [],
                "id": str(chief_req.icms_hmrc_id),
                "organisation": {
                    "address": {
                        "line_1": "I1 address line 1",
                        "line_2": "I1 address line 2",
                        "line_3": "",
                        "line_4": "",
                        "line_5": "",
                        "postcode": "BT180LZ",  # /PS-IGNORE
                    },
                    "end_date": None,
                    "eori_number": "GB0123456789ABCDE",
                    "name": "Test Importer 1",
                    "start_date": None,
                },
                "restrictions": "",
                "start_date": licence.licence_start_date.strftime("%Y-%m-%d"),
                "end_date": licence.licence_end_date.strftime("%Y-%m-%d"),
                "type": "SIL",
            }
        }

        case_progress.check_expected_task(app, Task.TaskType.CHIEF_WAIT)

    def test_send_application_to_chief_revoke_licence(self, completed_sil_app, monkeypatch):
        # Setup
        app = completed_sil_app
        document_pack.pack_active_revoke(app, "test revoke licence reason", False)
        licence = document_pack.pack_revoked_get(app)

        request_license_mock = mock.create_autospec(spec=client.request_license)
        monkeypatch.setattr(client, "request_license", request_license_mock)

        # Test
        client.send_application_to_chief(app, None, revoke_licence=True)

        # Asserts
        request_license_mock.assert_called_once()
        app.refresh_from_db()
        assert app.chief_references.count() == 1

        chief_req: ICMSHMRCChiefRequest = app.chief_references.first()

        assert chief_req.case_reference == app.reference

        assert chief_req.request_data == {
            "licence": {
                "action": "cancel",
                "reference": app.reference,
                "id": str(chief_req.icms_hmrc_id),
                "type": "SIL",
                "start_date": licence.licence_start_date.strftime("%Y-%m-%d"),
                "end_date": licence.licence_end_date.strftime("%Y-%m-%d"),
                "licence_reference": "GBSIL0000001B",
            }
        }

        case_progress.check_expected_task(app, Task.TaskType.CHIEF_REVOKE_WAIT)
