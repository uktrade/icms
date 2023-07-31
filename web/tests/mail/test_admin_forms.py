from unittest import mock
from uuid import UUID

import pytest

from web.admin import EmailTemplateForm
from web.mail.constants import EmailTypes
from web.models import EmailTemplate

FAKE_TEMPLATE_UUID = UUID("646bea34-20ef-437c-b001-ea557f3ba1e6")


@pytest.mark.django_db
def test_email_template_form_uuid_error():
    case_complete = EmailTemplate.objects.get(name=EmailTypes.CASE_COMPLETE)
    form = EmailTemplateForm(
        instance=case_complete,
        data={"gov_notify_template_id": "hello", "name": EmailTypes.CASE_COMPLETE},
    )
    assert form.is_valid() is False
    assert form.errors == {"gov_notify_template_id": ["Enter a valid UUID."]}


@pytest.mark.django_db
@mock.patch("web.admin.is_valid_template_id")
def test_email_template_id_is_invalid(mock_is_valid_template_id):
    mock_is_valid_template_id.return_value = False
    case_complete = EmailTemplate.objects.get(name=EmailTypes.CASE_COMPLETE)
    form = EmailTemplateForm(
        instance=case_complete,
        data={
            "gov_notify_template_id": FAKE_TEMPLATE_UUID,
            "name": EmailTypes.CASE_COMPLETE,
        },
    )
    assert form.is_valid() is False
    assert form.errors == {"gov_notify_template_id": ["GOV Notify template not found"]}
    mock_is_valid_template_id.assert_called_once_with(FAKE_TEMPLATE_UUID)


@pytest.mark.django_db
@mock.patch("web.admin.is_valid_template_id")
def test_email_template_id_is_valid(mock_is_valid_template_id):
    mock_is_valid_template_id.return_value = True
    case_complete = EmailTemplate.objects.get(name=EmailTypes.CASE_COMPLETE)
    form = EmailTemplateForm(
        instance=case_complete,
        data={
            "gov_notify_template_id": FAKE_TEMPLATE_UUID,
            "name": EmailTypes.CASE_COMPLETE,
        },
    )
    assert form.is_valid() is True, form.errors
    instance = form.save()
    mock_is_valid_template_id.assert_called_once_with(FAKE_TEMPLATE_UUID)
    assert str(instance) == EmailTypes.CASE_COMPLETE.label
    assert instance.gov_notify_template_id == FAKE_TEMPLATE_UUID
