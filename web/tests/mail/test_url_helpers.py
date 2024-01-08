import pytest
from django.utils import timezone

from web.domains.case.services import document_pack
from web.mail.url_helpers import (
    get_authority_view_url,
    get_case_view_url,
    get_constabulary_document_download_view_url,
    get_constabulary_document_view_url,
    get_mailshot_detail_view_url,
    get_validate_digital_signatures_url,
)
from web.models import FirearmsAuthority, Section5Authority
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


def test_get_mailshot_detail_view_url(draft_mailshot):
    expected_url = f"http://import-a-licence/mailshot/{draft_mailshot.pk}/received/"
    assert get_mailshot_detail_view_url(draft_mailshot, get_importer_site_domain()) == expected_url


@pytest.mark.parametrize(
    "authority_class,full_url,expected_url",
    [
        (Section5Authority, False, "/importer/section5/{pk}/view/"),
        (Section5Authority, True, "http://caseworker/importer/section5/{pk}/view/"),
        (FirearmsAuthority, False, "/importer/firearms/{pk}/view/"),
        (FirearmsAuthority, True, "http://caseworker/importer/firearms/{pk}/view/"),
    ],
)
def test_get_authority_view_url(authority_class, full_url, expected_url, importer):
    authority = authority_class.objects.create(
        importer=importer,
        start_date=timezone.now().date(),
        end_date=timezone.now().date(),
        archive_reason=["REVOKED", "WITHDRAWN"],
        other_archive_reason="Moved",
        reference="Test Authority",
    )
    assert get_authority_view_url(authority, full_url) == expected_url.format(pk=authority.pk)


@pytest.mark.parametrize(
    "full_url,expected_url",
    [
        (False, "/case/import/{pk}/documents/{doc_pack_pk}/"),
        (True, "http://caseworker/case/import/{pk}/documents/{doc_pack_pk}/"),
    ],
)
def test_get_constabulary_document_view_url(completed_dfl_app, full_url, expected_url):
    active_pack = document_pack.pack_active_get(completed_dfl_app)
    assert get_constabulary_document_view_url(
        completed_dfl_app, active_pack, full_url=full_url
    ) == expected_url.format(pk=completed_dfl_app.pk, doc_pack_pk=active_pack.pk)


@pytest.mark.parametrize(
    "full_url,expected_url",
    [
        (False, "/case/import/{pk}/documents/{doc_pack_pk}/download/{cdr_pk}/"),
        (True, "http://caseworker/case/import/{pk}/documents/{doc_pack_pk}/download/{cdr_pk}/"),
    ],
)
def test_get_constabulary_document_download_view_url(completed_dfl_app, full_url, expected_url):
    active_pack = document_pack.pack_active_get(completed_dfl_app)
    cdr = active_pack.document_references.first()
    assert get_constabulary_document_download_view_url(
        completed_dfl_app, active_pack, cdr, full_url=full_url
    ) == expected_url.format(pk=completed_dfl_app.pk, cdr_pk=cdr.pk, doc_pack_pk=active_pack.pk)
