from playwright.sync_api import Page

from web.end_to_end import conftest, types, utils
from web.forms.fields import JQUERY_DATE_FORMAT


def test_can_create_fa_dfl(
    pages: conftest.UserPages, sample_upload_file: types.FilePayload
) -> None:
    """End-to-end test for creating a FA-DFL application.

    This tests requires multiple pages as there is a back and forth between user types.
    """

    with pages.imp_page() as imp_page:
        dfl_id = fa_dfl_create(imp_page, sample_upload_file)

    with pages.ilb_page() as ilb_page:
        fa_dfl_manage_and_complete_case(ilb_page, dfl_id)


def get_applicant_reference(dfl_id: int) -> str:
    return f"fa_dfl_reference_{dfl_id}"


def fa_dfl_create(page: Page, sample_upload_file: types.FilePayload) -> int:
    page.get_by_role("link", name="New Import Application").click()
    utils.assert_page_url(page, "/import/")

    page.get_by_role("link", name="Deactivated Firearms Import Licence").click()
    utils.assert_page_url(page, "/import/create/firearms/dfl/")

    page.get_by_text("-- Select Importer").click()

    page.get_by_role("option", name="Dummy importer").click()

    page.get_by_role("combobox", name="-- Select Office").locator(
        'span[role="textbox"]:has-text("-- Select Office")'
    ).click()

    page.get_by_role(
        "option", name="3 Whitehall Pl\nWestminster\nLondon\nSW1A 2HP"  # /PS-IGNORE
    ).click()

    page.get_by_role("button", name="Create").click()

    dfl_id = utils.get_application_id(page.url, r"import/firearms/dfl/(?P<app_pk>\d+)/edit/")
    utils.assert_page_url(page, f"/import/firearms/dfl/{dfl_id}/edit/")

    page.get_by_label("Applicant's Reference", exact=False).click()

    page.get_by_label("Applicant's Reference", exact=False).fill(get_applicant_reference(dfl_id))

    page.get_by_label("Proof Checked").check()

    page.get_by_role("combobox", name="Country Of Origin").select_option("19")

    page.get_by_role("combobox", name="Country Of Consignment").select_option("24")

    page.get_by_role("combobox", name="Constabulary").select_option("74")

    page.get_by_role("button", name="Save").click()
    utils.assert_page_url(page, f"/import/firearms/dfl/{dfl_id}/edit/")

    page.get_by_role("link", name="Add Goods").click()
    utils.assert_page_url(page, f"/import/firearms/dfl/{dfl_id}/goods-certificate/add/")

    page.get_by_label("Goods Description").click()

    page.get_by_label("Goods Description").fill("test")

    page.get_by_label("Deactivated Certificate Reference").click()

    page.get_by_label("Deactivated Certificate Reference").fill("test")

    page.get_by_role("combobox", name="Issuing Country").select_option("23")

    page.get_by_label("Document").set_input_files(sample_upload_file)

    page.get_by_role("button", name="Save").click()
    utils.assert_page_url(page, f"/import/firearms/dfl/{dfl_id}/edit/")

    page.get_by_role("link", name="Details of Who Bought From").click()
    utils.assert_page_url(page, f"/import/firearms/fa/{dfl_id}/import-contacts/manage/")

    page.locator("#id_know_bought_from").get_by_text("No").click()

    page.get_by_role("button", name="Save").click()
    utils.assert_page_url(page, f"/import/firearms/fa/{dfl_id}/import-contacts/manage/")

    page.get_by_role("link", name="Submit").click()
    utils.assert_page_url(page, f"/import/firearms/dfl/{dfl_id}/submit/")

    page.get_by_label(
        'Confirm that you agree to the above by typing "I AGREE", in capitals, in this box'
    ).click()
    page.get_by_label(
        'Confirm that you agree to the above by typing "I AGREE", in capitals, in this box'
    ).fill("I AGREE")

    page.get_by_role("button", name="Submit Application").click()
    utils.assert_page_url(page, "/workbasket/")

    return dfl_id


def fa_dfl_manage_and_complete_case(page: Page, dfl_id: int) -> None:
    #
    # Complete Take Ownership
    #
    workbasket_row = utils.get_wb_row(page, dfl_id)
    workbasket_row.get_by_role("button", name="Take Ownership").click()
    utils.assert_page_url(page, f"/case/import/{dfl_id}/admin/manage/")

    #
    # Complete Checklist
    #
    page.get_by_role("link", name="Checklist").click()
    utils.assert_page_url(page, f"/import/firearms/dfl/{dfl_id}/checklist/")

    page.get_by_role("combobox", name="Deactivation certificate attached?").select_option("yes")
    page.get_by_role(
        "combobox", name="Deactivation certificate issued by competent authority?"
    ).select_option("yes")
    page.get_by_role("combobox", name="Case update required from applicant?").select_option("yes")
    page.get_by_role("combobox", name="Further information request required?").select_option("yes")
    page.get_by_label(
        "Response Preparation - approve/refuse the request, edit details if necessary"
    ).check()
    page.get_by_role("combobox", name="Validity period correct?").select_option("yes")
    page.get_by_role(
        "combobox",
        name="Correct endorsements listed? Add/edit/remove as required (changes are automatically saved)",
    ).select_option("yes")
    page.get_by_label(
        "Authorisation - start authorisation (close case processing) to authorise the licence. Errors logged must be resolved."
    ).check()
    page.get_by_role("button", name="Save").click()
    utils.assert_page_url(page, f"/import/firearms/dfl/{dfl_id}/checklist/")

    #
    # Complete Response Preparation (Approve application)
    #
    page.get_by_role("link", name="Response Preparation").click()
    utils.assert_page_url(page, f"/case/import/{dfl_id}/prepare-response/")

    page.get_by_role("combobox", name="Decision").select_option("APPROVE")
    page.get_by_role("button", name="Save").click()
    utils.assert_page_url(page, f"/case/import/{dfl_id}/prepare-response/")

    #
    # Complete Response Preparation (Licence Details)
    #
    page.locator('[data-test-id="edit-licence"]').click()
    utils.assert_page_url(page, f"/import/case/{dfl_id}/licence/edit")

    future_date = utils.get_future_datetime().date().strftime(JQUERY_DATE_FORMAT)
    page.get_by_label("Licence End Date").click()
    page.get_by_label("Licence End Date").fill(future_date)
    page.get_by_role("button", name="Done").click()

    page.get_by_role("combobox", name="Issue paper licence only?").select_option("true")
    page.get_by_role("button", name="Save").click()
    utils.assert_page_url(page, f"/case/import/{dfl_id}/prepare-response/")

    #
    # Complete Authorisation
    #
    page.get_by_role("link", name="Authorisation").click()
    utils.assert_page_url(page, f"/case/import/{dfl_id}/authorisation/start/")

    page.get_by_role("button", name="Start Authorisation (Close Case Processing)").click()
    utils.assert_page_url(page, "/workbasket/")

    #
    # Authorise Documents
    #
    workbasket_row = utils.get_wb_row(page, dfl_id)
    workbasket_row.get_by_role("link", name="Authorise Documents").click()
    utils.assert_page_url(page, f"/case/import/{dfl_id}/authorisation/authorise-documents/")

    page.get_by_label("Password").click()
    page.get_by_label("Password").fill("admin")
    page.get_by_role("button", name="Sign and Authorise").click()
    utils.assert_page_url(page, "/workbasket/")

    # Close the popup: "Authorise Success: Application xxx/xxxx/xxxxx has been queued for document signing"
    page.get_by_role("button", name="Close this message").click()
    page.get_by_role("link", name="Workbasket").click()
    utils.assert_page_url(page, "/workbasket/")

    #
    # Bypass CHIEF and check application complete
    #
    workbasket_row = utils.get_wb_row(page, dfl_id)
    workbasket_row.get_by_role("button", name="(TEST) Bypass CHIEF", exact=True).click()
    utils.assert_page_url(page, "/workbasket/")

    workbasket_row = utils.get_wb_row(page, dfl_id)
    workbasket_row.get_by_role("cell", name="Completed ").is_visible()
