import pytest

from web.mail.url_helpers import get_case_view_url, get_validate_digital_signatures_url
from web.sites import get_exporter_site_domain, get_importer_site_domain


@pytest.mark.parametrize(
    "full_url,expected_url",
    [
        (False, "/static/web/docs/ValidateDigSigs.pdf"),
        (True, "http://import-a-licence/static/web/docs/ValidateDigSigs.pdf"),
    ],
)
def test_get_validate_digital_signatures_url(db, full_url, expected_url):
    assert get_validate_digital_signatures_url(full_url=full_url) == expected_url


def test_get_export_case_view_url(completed_cfs_app):
    expected_url = f"http://export-a-certificate/case/export/{completed_cfs_app.pk}/view/"
    assert get_case_view_url(completed_cfs_app, get_exporter_site_domain()) == expected_url


def test_get_import_case_view_url(completed_dfl_app):
    expected_url = f"http://import-a-licence/case/import/{completed_dfl_app.pk}/view/"
    assert get_case_view_url(completed_dfl_app, get_importer_site_domain()) == expected_url


def test_get_case_view_url(completed_dfl_app):
    expected_url = f"/case/import/{completed_dfl_app.pk}/view/"
    assert get_case_view_url(completed_dfl_app, "") == expected_url
