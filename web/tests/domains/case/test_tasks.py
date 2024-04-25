import io
from unittest import mock

import PIL
import pytest
from PIL.PngImagePlugin import PngImageFile

from web.domains.case.services import case_progress, document_pack
from web.domains.case.shared import ImpExpStatus
from web.domains.case.tasks import (
    create_case_document_pack,
    update_application_on_error,
)
from web.domains.case.utils import end_process_task
from web.models import ICMSHMRCChiefRequest, Task, VariationRequest
from web.tests.helpers import add_variation_request_to_app


@pytest.fixture()
def dummy_signature_image():
    """Generate a dummy signature image for testing"""
    image = PIL.Image.new("RGBA", size=(50, 50), color=(256, 0, 0))
    image_file = io.BytesIO()
    image.save(image_file, "PNG")
    image_file.seek(0)
    return PngImageFile(image_file)


def sign_pre_signed_application(application, user):
    task = case_progress.get_expected_task(application, Task.TaskType.AUTHORISE)
    end_process_task(task, user)

    Task.objects.create(
        process=application, task_type=Task.TaskType.DOCUMENT_SIGNING, previous=task
    )


@mock.patch("web.utils.pdf.signer.get_active_signature_image")
@mock.patch("web.domains.case.tasks.delete_file_from_s3")
@mock.patch("web.domains.case.tasks.upload_file_obj_to_s3")
def test_fa_dfl_create_case_document_pack(
    mock_upload_file_obj_to_s3,
    mock_delete_file_from_s3,
    mock_get_active_signature_image,
    dummy_signature_image,
    fa_dfl_app_pre_sign,
    ilb_admin_user,
):
    application = fa_dfl_app_pre_sign

    sign_pre_signed_application(application, ilb_admin_user)

    # Mock return value for dummy signature and file size
    mock_get_active_signature_image.return_value = dummy_signature_image
    mock_upload_file_obj_to_s3.return_value = 100

    create_case_document_pack(application, ilb_admin_user)

    mock_delete_file_from_s3.assert_not_called()
    mock_upload_file_obj_to_s3.assert_called()
    assert mock_upload_file_obj_to_s3.call_count == 2

    application.refresh_from_db()

    # Check the documents have been created
    pack = document_pack.pack_draft_get(application)
    licence = document_pack.doc_ref_licence_get(pack)
    cover_letter = document_pack.doc_ref_cover_letter_get(pack)
    assert licence.document.filename == "import-licence.pdf"
    assert cover_letter.document.filename == "cover-letter.pdf"

    # Check this application is with chief.
    case_progress.check_expected_status(application, [ImpExpStatus.PROCESSING])
    case_progress.get_expected_task(application, Task.TaskType.CHIEF_WAIT)
    assert ICMSHMRCChiefRequest.objects.filter(
        import_application=application, status=ICMSHMRCChiefRequest.CHIEFStatus.PROCESSING
    ).exists()


def test_fa_dfl_update_application_on_error(fa_dfl_app_pre_sign, ilb_admin_user):
    application = fa_dfl_app_pre_sign

    sign_pre_signed_application(application, ilb_admin_user)

    update_application_on_error(application_pk=application.pk, user_pk=ilb_admin_user.pk)

    application.refresh_from_db()

    case_progress.check_expected_status(application, [ImpExpStatus.PROCESSING])
    case_progress.check_expected_task(application, Task.TaskType.DOCUMENT_ERROR)


@mock.patch("web.domains.case.tasks.send_completed_application_process_notifications")
@mock.patch("web.utils.pdf.signer.get_active_signature_image")
@mock.patch("web.domains.case.tasks.delete_file_from_s3")
@mock.patch("web.domains.case.tasks.upload_file_obj_to_s3")
def test_cfs_create_case_document_pack(
    mock_upload_file_obj_to_s3,
    mock_delete_file_from_s3,
    mock_get_active_signature_image,
    mock_send_completed_application_process_notifications,
    dummy_signature_image,
    cfs_app_pre_sign,
    ilb_admin_user,
):
    application = cfs_app_pre_sign

    sign_pre_signed_application(application, ilb_admin_user)

    # Mock return value for dummy signature and file size
    mock_get_active_signature_image.return_value = dummy_signature_image
    mock_upload_file_obj_to_s3.return_value = 100

    create_case_document_pack(application, ilb_admin_user)

    mock_delete_file_from_s3.assert_not_called()
    mock_upload_file_obj_to_s3.assert_called()
    assert mock_upload_file_obj_to_s3.call_count == 2
    mock_send_completed_application_process_notifications.assert_called_once_with(application)

    application.refresh_from_db()

    # Check the documents have been created
    pack = document_pack.pack_active_get(application)
    certificates = document_pack.doc_ref_certificates_all(pack)
    assert certificates.count() == 2

    assert [cert.document.filename for cert in certificates] == [
        "Certificate of Free Sale (Afghanistan).pdf",
        "Certificate of Free Sale (Zimbabwe).pdf",
    ]

    # Check this application is complete.
    case_progress.check_expected_status(application, [ImpExpStatus.COMPLETED])
    assert case_progress.get_active_tasks(application).count() == 0


@mock.patch("web.domains.case.tasks.send_completed_application_process_notifications")
@mock.patch("web.utils.pdf.signer.get_active_signature_image")
@mock.patch("web.domains.case.tasks.delete_file_from_s3")
@mock.patch("web.domains.case.tasks.upload_file_obj_to_s3")
def test_cfs_create_case_document_pack_variation_request(
    mock_upload_file_obj_to_s3,
    mock_delete_file_from_s3,
    mock_get_active_signature_image,
    mock_send_completed_application_process_notifications,
    dummy_signature_image,
    cfs_app_pre_sign,
    ilb_admin_user,
):
    application = cfs_app_pre_sign
    application.status = ImpExpStatus.VARIATION_REQUESTED
    application.save()
    application_variation = add_variation_request_to_app(application, ilb_admin_user)
    sign_pre_signed_application(application, ilb_admin_user)

    # Mock return value for dummy signature and file size
    mock_get_active_signature_image.return_value = dummy_signature_image
    mock_upload_file_obj_to_s3.return_value = 100

    create_case_document_pack(application, ilb_admin_user)

    mock_delete_file_from_s3.assert_not_called()
    mock_upload_file_obj_to_s3.assert_called()
    assert mock_upload_file_obj_to_s3.call_count == 2
    mock_send_completed_application_process_notifications.assert_called_once_with(application)

    application.refresh_from_db()
    application_variation.refresh_from_db()

    # Check the documents have been created
    pack = document_pack.pack_active_get(application)
    certificates = document_pack.doc_ref_certificates_all(pack)
    assert certificates.count() == 2

    assert [cert.document.filename for cert in certificates] == [
        "Certificate of Free Sale (Afghanistan).pdf",
        "Certificate of Free Sale (Zimbabwe).pdf",
    ]

    # Check this application is complete.
    case_progress.check_expected_status(application, [ImpExpStatus.COMPLETED])
    assert case_progress.get_active_tasks(application).count() == 0
    case_progress.check_expected_status(application, [ImpExpStatus.COMPLETED])

    # check the variation request is closed
    assert application_variation.status == VariationRequest.Statuses.CLOSED


def test_cfs_update_application_on_error(cfs_app_pre_sign, ilb_admin_user):
    application = cfs_app_pre_sign

    sign_pre_signed_application(application, ilb_admin_user)

    update_application_on_error(application_pk=application.pk, user_pk=ilb_admin_user.pk)

    application.refresh_from_db()

    case_progress.check_expected_status(application, [ImpExpStatus.PROCESSING])
    case_progress.check_expected_task(application, Task.TaskType.DOCUMENT_ERROR)
