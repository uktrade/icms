import re

from playwright.sync_api import Page

from web.end_to_end import conftest, types, utils
from web.forms.fields import JQUERY_DATE_FORMAT


def test_can_create_sanctions(
    pages: conftest.UserPages, sample_upload_file: types.FilePayload
) -> None:
    """End-to-end test for creating a Sanctions and Adhoc application.

    This tests requires multiple pages as there is a back and forth between user types.
    """

    with pages.imp_page() as imp_page:
        app_id = sanctions_create(imp_page, sample_upload_file)

    with pages.ilb_page() as ilb_page:
        sanctions_manage_and_complete_case(ilb_page, app_id)


def sanctions_create(page: Page, sample_upload_file: types.FilePayload) -> int:
    #
    # Create application
    #
    page.get_by_role("link", name="New Import Application").click()
    page.get_by_role("link", name="Sanctions and Adhoc Licence Application").click()

    #
    # Set importer
    #
    page.get_by_text("-- Select Importer").click()
    page.get_by_role("option", name="Dummy importer").click()
    page.get_by_role("combobox", name="-- Select Office").get_by_text("-- Select Office").click()
    page.get_by_role(
        "option", name="3 Whitehall Pl\nWestminster\nLondon\nSW1A 2HP"  # /PS-IGNORE
    ).click()
    page.get_by_role("button", name="Create").click()

    # store the primary key to return later
    app_id = utils.get_application_id(page.url, r"import/sanctions/(?P<app_pk>\d+)/edit/")

    #
    # Fill in main application page
    #
    page.get_by_label("Applicant's Reference").click()
    page.get_by_label("Applicant's Reference").fill("Applicant's reference value")
    page.get_by_role("combobox", name="Country Of Origin").select_option("76")
    page.get_by_role("combobox", name="Country Of Consignment").select_option("1")
    page.get_by_label("Exporter Name").click()
    page.get_by_label("Exporter Name").fill("Exporter name")
    page.get_by_label("Exporter Address").click()
    page.get_by_label("Exporter Address").fill("Exporter address")
    page.get_by_role("button", name="Save").click()

    #
    # Add a goods line
    #
    page.get_by_role("link", name="Add Goods").click()
    page.get_by_role("combobox", name="Commodity Code").select_option("2267")
    page.get_by_label("Goods Description").click()
    page.get_by_label("Goods Description").fill("Goods description value")
    page.get_by_label("Quantity").click()
    page.get_by_label("Quantity").fill("12345")
    page.get_by_label("Value (GBP CIF)").click()
    page.get_by_label("Value (GBP CIF)").fill("54321")
    page.get_by_role("button", name="Save").click()
    page.get_by_role("link", name="Add Supporting Document").click()
    page.get_by_label("Document").set_input_files(sample_upload_file)
    page.get_by_role("button", name="Save").click()

    #
    # Submit
    #
    page.get_by_role("link", name="Submit").click()
    page.get_by_label(
        'Confirm that you agree to the above by typing "I AGREE", in capitals, in this box'
    ).click()
    page.get_by_label(
        'Confirm that you agree to the above by typing "I AGREE", in capitals, in this box'
    ).fill("I AGREE")
    page.get_by_role("button", name="Submit Application").click()

    #
    # Check popup appears
    #
    page.get_by_text(
        "Your application has been submitted. The reference number assigned to this case "
    ).click()
    page.get_by_role("button", name="Close this message").click()

    return app_id


def sanctions_manage_and_complete_case(page: Page, app_id) -> None:
    #
    # Complete Take Ownership
    #
    workbasket_row = utils.get_wb_row(page, app_id)
    workbasket_row.get_by_role("button", name="Take Ownership").click()

    #
    # Complete Response Preparation (Approve application)
    #
    page.get_by_role("link", name="Response Preparation").click()
    page.get_by_role("combobox", name="Decision").select_option("APPROVE")
    page.get_by_role("button", name="Save").click()

    #
    # Complete Response Preparation (Licence Details)
    #
    page.locator('[data-test-id="edit-licence"]').click()

    future_date = utils.get_future_datetime().date().strftime(JQUERY_DATE_FORMAT)
    page.get_by_label("Licence End Date").click()
    page.get_by_label("Licence End Date").fill(future_date)
    page.get_by_role("button", name="Done").click()
    page.get_by_role("button", name="Save").click()

    #
    # Add an Endorsement
    #
    page.get_by_role("link", name=re.compile(".+Add Endorsement")).click()
    page.get_by_role("combobox", name="Content").select_option("54")
    page.get_by_role("button", name="Save").click()

    #
    # Add a custom Endorsement
    #
    page.get_by_role("link", name=re.compile(".+Add Custom Endorsement")).click()
    page.get_by_label("Content").click()
    page.get_by_label("Content").fill("Custom endorsement.")
    page.get_by_role("button", name="Save").click()

    #
    # Complete Authorisation
    #
    page.get_by_role("link", name="Authorisation").click()
    page.get_by_role("button", name="Start Authorisation (Close Case Processing)").click()

    #
    # Authorise Documents
    #
    workbasket_row = utils.get_wb_row(page, app_id)
    workbasket_row.get_by_role("link", name="Authorise Documents").click()
    page.get_by_role("button", name="Sign and Authorise").click()
    page.get_by_role("button", name="OK").click()

    # Close the popup: "Authorise Success: Application xxx/xxxx/xxxxx has been queued for document signing"
    page.get_by_role("button", name="Close this message").click()

    # Annoying bug causing test to fail.
    # Wait for networkidle and then reload the workbasket to see the bypass CHIEF link
    page.wait_for_load_state("networkidle")
    page.get_by_role("link", name="Workbasket").click()

    utils.assert_page_url(page, "/workbasket/")

    #
    # Bypass CHIEF and check application complete
    #
    workbasket_row = utils.get_wb_row(page, app_id)
    workbasket_row.get_by_role("button", name="(TEST) Bypass CHIEF", exact=True).click()

    workbasket_row = utils.get_wb_row(page, app_id)
    workbasket_row.get_by_role("cell", name="Completed ").is_visible()
