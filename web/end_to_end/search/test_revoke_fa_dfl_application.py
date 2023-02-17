from playwright.sync_api import Page

from web.end_to_end import conftest, types, utils
from web.end_to_end.case.import_app.test_create_fa_dfl_application import (
    fa_dfl_create,
    fa_dfl_manage_and_complete_case,
    get_applicant_reference,
)


def test_can_revoke_fa_dfl_application(
    pages: conftest.UserPages, sample_upload_file: types.FilePayload
) -> None:
    """End-to-end test for revoking a FA-DFL application.

    This tests requires multiple pages as there is a back and forth between user types.
    """

    with pages.imp_page() as imp_page:
        dfl_id = fa_dfl_create(imp_page, sample_upload_file)

    with pages.ilb_page() as ilb_page:
        fa_dfl_manage_and_complete_case(ilb_page, dfl_id)
        revoke_fa_dfl_application(ilb_page, dfl_id)


def revoke_fa_dfl_application(page: Page, dfl_id: int) -> None:
    #
    # Navigate to search screen
    #
    page.get_by_role("link", name="Search").first.click()
    page.get_by_role("link", name="Search Import Applications").click()

    #
    # Search for application
    #
    reference = get_applicant_reference(dfl_id)
    page.get_by_role("link", name="Enable advanced search").click()
    page.get_by_label("Applicant's Reference").click()
    page.get_by_label("Applicant's Reference").fill(reference)
    page.get_by_role("button", name="Search").click()

    #
    # Click revoke licence
    #
    search_row = utils.get_search_row(page, dfl_id)
    search_row.get_by_role("link", name="Revoke Licence").click()

    #
    # Submit revoke licence form
    #
    page.get_by_label("Email Applicants?").check()
    page.get_by_label("Reason").click()
    page.get_by_label("Reason").fill("Test revoke reason")
    page.get_by_role("button", name="Revoke Licence").click()

    #
    # Check the application has the revoked status
    #
    search_row = utils.get_search_row(page, dfl_id)
    search_row.get_by_text("Revoked").click()
