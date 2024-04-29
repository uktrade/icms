import datetime as dt
import os
import re

from playwright.sync_api import Page

from web.end_to_end import conftest, types, utils


def test_can_create_fa_oil(
    pages: conftest.UserPages, sample_upload_file: types.FilePayload
) -> None:
    """End-to-end test for creating a FA-OIL application.

    This tests requires multiple pages as there is a back and forth between user types.
    """

    with pages.imp_page() as imp_page:
        app_id = fa_oil_create(imp_page, sample_upload_file)

    with pages.ilb_page() as ilb_page:
        fa_oil_manage_and_complete_case(ilb_page, app_id)


def fa_oil_create(page: Page, sample_upload_file: types.FilePayload) -> int:
    #
    # Create application
    #
    page.get_by_role("link", name="New Import Application").click()
    page.get_by_role("link", name="Open Individual Import Licence").click()

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
    app_id = utils.get_application_id(page.url, r"import/firearms/oil/(?P<app_pk>\d+)/edit/")

    #
    # Fill in main application page
    #
    page.get_by_label("Applicant's Reference").click()
    page.get_by_label("Applicant's Reference").fill("Applicant's reference value")
    page.wait_for_timeout(100)
    page.get_by_role("button", name="Save").click()

    #
    # Add a certificate
    #
    page.get_by_role("link", name="Certificates").click()
    page.get_by_role("link", name="Add Certificate").click()
    page.get_by_label("Certificate Reference").click()
    page.get_by_label("Certificate Reference").fill("Certificate reference value")
    page.get_by_role("combobox", name="Constabulary").select_option("1")

    future_date = utils.get_future_datetime().date()
    issue_date = future_date.strftime(utils.JQUERY_DATE_FORMAT)
    expiry_date = dt.date(future_date.year + 1, 1, 1).strftime(utils.JQUERY_DATE_FORMAT)
    page.get_by_label("Date Issued").click()
    page.get_by_label("Date Issued").fill(issue_date)
    page.get_by_label("Date Issued").press("Enter")
    page.get_by_label("Expiry Date").click()
    page.get_by_label("Expiry Date").fill(expiry_date)
    page.get_by_label("Expiry Date").press("Enter")
    page.get_by_label("Document").set_input_files(sample_upload_file)
    page.get_by_role("button", name="Save").click()

    #
    # Complete Details of Who Bought From section
    #
    page.get_by_role("link", name="Details of Who Bought From").click()
    page.get_by_label("Yes").check()
    page.get_by_role("button", name="Save").click()

    #
    # Add a Legal Person
    #
    page.get_by_role("link", name="Add Who Bought From (Legal Person)").click()
    page.get_by_label("Name of Legal Person").click()
    page.get_by_label("Name of Legal Person").fill("Legal Person value")
    page.get_by_label("Registration Number").click()
    page.get_by_label("Registration Number").fill("Registration Number value")
    page.get_by_label("Street and Number").click()
    page.get_by_label("Street and Number").fill("1 street")
    page.get_by_label("Town/City").click()
    page.get_by_label("Town/City").fill("Town")
    page.get_by_label("Postcode").click()
    page.get_by_label("Postcode").fill("s1122z")
    page.get_by_label("Region").click()
    page.get_by_label("Region").fill("Yorkshire")
    page.get_by_role("combobox", name="Country").select_option("1")
    page.get_by_role("combobox", name="Did you buy from a dealer?").select_option("no")
    page.get_by_role("button", name="Save").click()

    #
    # Add a Natural Person
    #
    page.get_by_role("link", name="Add Who Bought From (Natural Person)").click()
    page.get_by_label("First Name").click()  # /PS-IGNORE
    page.get_by_label("First Name").fill("First name value")  # /PS-IGNORE
    page.get_by_label("Surname").click()
    page.get_by_label("Surname").fill("Surname value")
    page.get_by_label("Street and Number").click()
    page.get_by_label("Street and Number").fill("1 Street")
    page.get_by_label("Town/City").click()
    page.get_by_label("Town/City").fill("Town")
    page.get_by_label("Postcode").click()
    page.get_by_label("Postcode").fill("S12ZZ")  # /PS-IGNORE
    page.get_by_label("Region").click()
    page.get_by_label("Region").fill("Yorkshire")
    page.get_by_role("combobox", name="Country").select_option("1")
    page.get_by_role("combobox", name="Did you buy from a dealer?").select_option("no")
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


def fa_oil_manage_and_complete_case(page: Page, app_id: int) -> None:
    #
    # Complete Take Ownership
    #
    workbasket_row = utils.get_wb_row(page, app_id)
    workbasket_row.get_by_role("button", name="Take Ownership").click()

    #
    # Complete Checklist
    #
    page.get_by_role("link", name="Checklist").click()
    page.get_by_role("combobox", name="Authority to possess required?").select_option("yes")
    page.get_by_role("combobox", name="Authority to possess received?").select_option("no")
    page.get_by_role("combobox", name="Authority to possess checked with police?").select_option(
        "n/a"
    )
    page.get_by_role("combobox", name="Case update required from applicant?").select_option("yes")
    page.get_by_role("combobox", name="Further information request required?").select_option("no")
    page.get_by_label(
        "Response Preparation - approve/refuse the request, edit details if necessary"
    ).check()
    page.get_by_role(
        "combobox", name="Validity period of licence matches that of the RFD certificate?"
    ).select_option("n/a")
    page.get_by_role(
        "combobox",
        name="Correct endorsements listed? Add/edit/remove as required (changes are automatically saved)",
    ).select_option("yes")
    page.get_by_label(
        "Authorisation - start authorisation (close case processing) to authorise the licence. Errors logged must be resolved."
    ).check()
    page.get_by_role("button", name="Save").click()

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
    utils.set_licence_end_date(page)
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
    page.get_by_role("button", name="OK", exact=True).click()

    # Annoying bug causing test to fail.
    # Wait for networkidle and then reload the workbasket to see the bypass CHIEF link
    page.wait_for_load_state("networkidle")
    page.get_by_role("link", name="Workbasket").click()

    # Supplied when running end-to-end tests for CHIEF.
    if "CHIEF_END_TO_END_TEST" in os.environ:
        return

    #
    # Bypass CHIEF and check application complete
    #
    utils.bypass_chief(page, app_id)
    utils.assert_page_url(page, "/workbasket/")

    workbasket_row = utils.get_wb_row(page, app_id)
    workbasket_row.get_by_role("cell", name="Completed ").is_visible()
