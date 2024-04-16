import uuid

import freezegun
import pytest
from pytest_django.asserts import assertFormError

from web.domains.case.forms import DownloadDFLCaseDocumentsForm
from web.domains.case.services import document_pack
from web.models import Constabulary, ImportApplicationDownloadLink


@pytest.fixture()
def constabulary(db) -> Constabulary:
    return Constabulary.objects.get(name="Derbyshire")


@pytest.fixture()
def link(completed_dfl_app, constabulary) -> ImportApplicationDownloadLink:
    return ImportApplicationDownloadLink.objects.create(
        check_code=12345678,
        email="test_user@example.com",  # /PS-IGNORE
        constabulary=constabulary,
        licence=document_pack.pack_active_get(completed_dfl_app),
    )


def test_form_valid(link):
    data = {
        "email": link.email,
        "constabulary": link.constabulary_id,
        "check_code": link.check_code,
    }
    form = DownloadDFLCaseDocumentsForm(code=link.code, data=data)

    assert form.is_valid()


def test_form_invalid(link):
    data = {}
    form = DownloadDFLCaseDocumentsForm(code=link.code, data=data)

    assert not form.is_valid()
    assert len(form.errors) == 3

    for field in ["check_code", "constabulary", "email"]:
        assertFormError(form, field, "You must enter this item")


def test_form_invalid_for_unknown_code(caplog, constabulary):
    data = {
        "email": "test_user@example.com",  # /PS-IGNORE
        "constabulary": constabulary.id,
        "check_code": 12345678,
    }
    form = DownloadDFLCaseDocumentsForm(code=str(uuid.uuid4()), data=data)

    assert not form.is_valid()

    assert_common_error(form)
    assert_form_validation_error(caplog, "Invalid code or expired link")


def test_form_invalid_for_expired_link(caplog, constabulary, link):
    data = {
        "email": link.email,
        "constabulary": link.constabulary_id,
        "check_code": link.check_code,
    }
    link.expired = True
    link.save()

    form = DownloadDFLCaseDocumentsForm(code=link.code, data=data)

    assert not form.is_valid()

    assert_common_error(form)
    assert_form_validation_error(caplog, "Invalid code or expired link")


def test_form_invalid_for_invalid_form_data_with_valid_link(caplog, constabulary, link):
    data = {
        "email": link.email,
        "constabulary": link.constabulary_id,
        "check_code": 87654321,
    }

    form = DownloadDFLCaseDocumentsForm(code=link.code, data=data)

    assert not form.is_valid()

    assert_common_error(form)
    assert_form_validation_error(caplog, "Form data doesn't match link code")


def test_form_invalid_for_links_older_than_six_weeks(caplog, constabulary, link):
    # Recreate the link (with the time frozen in the past)
    # Can't override an auto_now_add datatime another way.
    with freezegun.freeze_time("2020-01-01"):
        link.pk = None
        link._state.adding = True
        link.code = uuid.uuid4()
        link.save()

    data = {
        "email": link.email,
        "constabulary": link.constabulary_id,
        "check_code": link.check_code,
    }
    form = DownloadDFLCaseDocumentsForm(code=link.code, data=data)

    assert not form.is_valid()

    assert_common_error(form)
    assert_form_validation_error(caplog, "Link created more than six weeks ago")


def assert_common_error(form):
    assert len(form.errors) == 1

    assertFormError(form, None, form.ERROR_MSG)


def assert_form_validation_error(caplog, msg):
    assert len(caplog.messages) == 1
    assert caplog.messages[0] == f"DownloadDFLCaseDocumentsForm link error: {msg}"
