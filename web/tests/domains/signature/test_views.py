from http import HTTPStatus
from unittest.mock import patch

import freezegun
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from faker import Faker

from web.models import Signature

fake = Faker()


def _add_dummy_signature(user, name=""):
    return Signature.objects.create(
        is_active=False,
        filename=fake.file_name(),
        content_type=fake.mime_type(),
        file_size=fake.pyint(),
        path=fake.file_path(),
        created_by=user,
        name=name or fake.name(),
        signatory=fake.name(),
        history="",
    )


def test_create_signature_page(ilb_admin_client):
    client = ilb_admin_client
    response = client.get(reverse("signature-create"))
    assert response.status_code == HTTPStatus.OK
    assert "<h4>Add new signature</h4" in str(response.content)


@freezegun.freeze_time("2023-12-19 12:51:59")
def test_create_first_signature(db, ilb_admin_client, ilb_admin_user, active_signature):
    active_signature.delete()
    client = ilb_admin_client
    post_data = {
        "name": "Test Signature",
        "signatory": "Test Signatory",
        "file": SimpleUploadedFile("myimage.jpeg", b"file_content"),
        "is_active": "on",
    }
    response = client.post(reverse("signature-create"), post_data, follow=True)
    content = str(response.content)

    assert "<h3>Signature Management</h3>" in content

    new_signature = Signature.objects.get(name="Test Signature")
    assert new_signature.is_active is True
    assert (
        new_signature.history
        == f'2023-12-19 12:51:59 - Signature "Test Signature" added by {ilb_admin_user} and set to the active signature.'
    )


@freezegun.freeze_time("2023-12-19 12:51:59")
def test_create_inactive_signature(db, ilb_admin_client, ilb_admin_user, active_signature):
    client = ilb_admin_client
    post_data = {
        "name": "Test Signature",
        "signatory": "Test Signatory",
        "file": SimpleUploadedFile("myimage.jpeg", b"file_content"),
    }
    response = client.post(reverse("signature-create"), post_data, follow=True)
    content = str(response.content)

    assert "<h3>Signature Management</h3>" in content

    new_signature = Signature.objects.get(name="Test Signature")
    assert new_signature.is_active is False
    assert (
        new_signature.history
        == f'2023-12-19 12:51:59 - Signature "Test Signature" added by {ilb_admin_user} but is not set to the active signature.'
    )
    assert Signature.objects.get(is_active=True) == active_signature


@freezegun.freeze_time("2023-12-19 12:51:59")
def test_create_active_signature(db, ilb_admin_client, ilb_admin_user, active_signature):
    client = ilb_admin_client
    post_data = {
        "name": "Test Signature",
        "signatory": "Test Signatory",
        "file": SimpleUploadedFile("myimage.jpg", b"file_content"),
        "is_active": "on",
    }
    response = client.post(reverse("signature-create"), post_data, follow=True)
    active_signature.refresh_from_db()
    content = str(response.content)

    assert "<h3>Signature Management</h3>" in content
    new_signature = Signature.objects.get(name="Test Signature")
    assert new_signature.is_active is True
    assert new_signature.history == (
        f'2023-12-19 12:51:59 - Signature "Test Signature" added by {ilb_admin_user} and set to the active signature. '
        f'Replaces signature "{active_signature.name}"'
    )
    assert Signature.objects.get(name="Test Signature", is_active=True)
    assert active_signature.is_active is False
    active_signature_history = active_signature.history.split("\n")[0]
    assert (
        active_signature_history
        == f'2023-12-19 12:51:59 - Archived by {ilb_admin_user}. Replaced by signature "Test Signature"'
    )


@patch("web.domains.signature.views.get_signature_file_base64")
def test_view_signture(mock_get_file, db, ilb_admin_client, active_signature):
    mock_get_file.return_value == ""
    client = ilb_admin_client
    response = client.get(reverse("signature-view", kwargs={"signature_pk": active_signature.pk}))
    assert response.status_code == HTTPStatus.OK


@freezegun.freeze_time("2023-12-19 12:51:59")
def test_set_active_signature(db, ilb_admin_client, ilb_admin_user, active_signature):
    client = ilb_admin_client
    signature = _add_dummy_signature(ilb_admin_user)
    response = client.post(
        reverse("signature-set-active", kwargs={"signature_pk": signature.pk}), follow=True
    )
    content = str(response.content)
    signature.refresh_from_db()
    active_signature.refresh_from_db()

    assert "<h3>Signature Management</h3>" in content
    assert f'Signature "{signature.name}" is set to the active signature.' in content
    assert signature.is_active is True
    assert (
        signature.history
        == f'2023-12-19 12:51:59 - Set active by {ilb_admin_user}. Replaces signature "{active_signature.name}"'
    )
    assert active_signature.is_active is False
    assert (
        active_signature.history.split("\n")[0]
        == f'2023-12-19 12:51:59 - Archived by {ilb_admin_user}. Replaced by signature "{signature.name}"'
    )


def test_set_active_signature_currently_active(db, ilb_admin_client, active_signature):
    client = ilb_admin_client
    response = client.post(
        reverse("signature-set-active", kwargs={"signature_pk": active_signature.pk}), follow=True
    )
    content = str(response.content)

    assert "<h3>Signature Management</h3>" in content
    assert f'Signature "{active_signature.name}" is already the active signature.' in content


@freezegun.freeze_time("2023-12-19 12:51:59")
def test_set_active_signature_no_currently_active(
    db, ilb_admin_client, ilb_admin_user, active_signature
):
    active_signature.delete()
    client = ilb_admin_client
    signature = _add_dummy_signature(ilb_admin_user)
    response = client.post(
        reverse("signature-set-active", kwargs={"signature_pk": signature.pk}), follow=True
    )
    content = str(response.content)
    signature.refresh_from_db()

    assert "<h3>Signature Management</h3>" in content
    assert f'Signature "{signature.name}" is set to the active signature.' in content
    assert signature.is_active is True
    assert signature.history == f"2023-12-19 12:51:59 - Set active by {ilb_admin_user}."
