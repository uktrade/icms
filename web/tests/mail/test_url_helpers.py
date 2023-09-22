import pytest

from web.mail.url_helpers import get_case_view_url, get_validate_digital_signatures_url


@pytest.mark.parametrize(
    "full_url,expected_url",
    [
        (False, "/static/web/docs/ValidateDigSigs.pdf"),
        (True, "http://caseworker/static/web/docs/ValidateDigSigs.pdf"),
    ],
)
def test_get_validate_digital_signatures_url(db, full_url, expected_url):
    assert get_validate_digital_signatures_url(full_url=full_url) == expected_url


@pytest.mark.parametrize(
    "application,full_url,expected_url",
    [
        ("completed_cfs_app", False, "/case/export/{pk}/view/"),
        ("completed_cfs_app", True, "http://export-a-certificate/case/export/{pk}/view/"),
        ("completed_dfl_app", False, "/case/import/{pk}/view/"),
        ("completed_dfl_app", True, "http://import-a-licence/case/import/{pk}/view/"),
    ],
)
def test_get_case_view_url(application, full_url, expected_url, request):
    application = request.getfixturevalue(application)
    expected_url = expected_url.format(pk=application.pk)
    assert get_case_view_url(application, full_url=full_url) == expected_url
