import datetime as dt
import os
import re

from playwright.sync_api import Page

from web.end_to_end import conftest, types, utils
from web.forms.fields import JQUERY_DATE_FORMAT


def test_can_create_fa_sil(
    pages: conftest.UserPages, sample_upload_file: types.FilePayload
) -> None:
    """End-to-end test for creating a FA-SIL application.

    This tests requires multiple pages as there is a back and forth between user types.
    """

    with pages.imp_page() as imp_page:
        app_id = fa_sil_create(imp_page, sample_upload_file)

    with pages.ilb_page() as ilb_page:
        fa_sil_manage_and_complete_case(ilb_page, app_id)


def fa_sil_create(page: Page, sample_upload_file: types.FilePayload) -> int:
    #
    # Create application
    #
    page.get_by_role("link", name="New Import Application").click()
    page.get_by_role("link", name="Specific Individual Import Licence").click()

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
    app_id = utils.get_application_id(page.url, r"import/firearms/sil/(?P<app_pk>\d+)/edit/")

    #
    # Fill in main application page
    #
    page.wait_for_load_state(state="domcontentloaded")
    page.get_by_label("Applicant's Reference").click()
    page.get_by_label("Applicant's Reference").fill("Applicant reference value")
    page.get_by_label("Section 1").check()
    page.get_by_label("Section 2").check()
    page.get_by_label("Section 5", exact=True).check()
    page.get_by_label("Section 58(2) - Obsolete Calibre").check()
    page.get_by_label("Section 58(2) - Other").check()
    page.get_by_label("Other Section Description").click()
    page.get_by_label("Other Section Description").fill("Other Section Description value")
    page.get_by_role("combobox", name="Country Of Origin").select_option("1")
    page.get_by_role("combobox", name="Country Of Consignment").select_option("2")
    page.locator("#id_military_police_0").check()
    page.locator("#id_eu_single_market").get_by_text("Yes").click()
    page.locator("#id_eu_single_market").get_by_text("No").click()
    page.locator("#id_manufactured").get_by_text("Yes").click()
    page.get_by_label("Additional comments").click()
    page.get_by_label("Additional comments").fill("Additional comments")
    page.get_by_role("button", name="Save").click()

    #
    # Add goods with quantity and unlimited quantity for each section
    #

    # Section 1
    page.get_by_role("link", name="Add Goods Item").click()
    page.get_by_role("link", name="Section 1").click()
    page.get_by_label("No").check()
    page.get_by_label("Description").click()
    page.get_by_label("Description").fill("Section 1 Goods")
    page.get_by_label("Quantity", exact=True).click()
    page.get_by_label("Quantity", exact=True).fill("5")
    page.get_by_role("button", name="Save").click()

    page.get_by_role("link", name="Add Goods Item").click()
    page.get_by_role("link", name="Section 1").click()
    page.get_by_label("No").check()
    page.get_by_label("Description").click()
    page.get_by_label("Description").fill("Section 1 Goods Unlimited")
    page.get_by_label("Unlimited Quantity").check()
    page.get_by_role("button", name="Save").click()

    # Section 2
    page.get_by_role("link", name="Add Goods Item").click()
    page.get_by_role("link", name="Section 2").click()
    page.get_by_label("No").check()
    page.get_by_label("Description").click()
    page.get_by_label("Description").fill("Section 2 Goods")
    page.get_by_label("Quantity", exact=True).click()
    page.get_by_label("Quantity", exact=True).fill("12345")
    page.get_by_role("button", name="Save").click()

    page.get_by_role("link", name="Add Goods Item").click()
    page.get_by_role("link", name="Section 2").click()
    page.get_by_label("No").check()
    page.get_by_label("Description").click()
    page.get_by_label("Description").fill("Section 2 Goods Unlimited")
    page.get_by_label("Unlimited Quantity").check()
    page.get_by_role("button", name="Save").click()

    # Section 5
    page.get_by_role("link", name="Add Goods Item").click()
    page.get_by_role("link", name="Section 5").first.click()
    page.get_by_role("textbox", name="---------").click()
    page.get_by_role(
        "option",
        name="5(1)(a) Any firearm capable of burst- or fully automatic fire and component parts of these.",
    ).click()
    page.get_by_label("No").check()
    page.get_by_label("Description").click()
    page.get_by_label("Description").fill("Section 5 Goods")
    page.get_by_label("Quantity", exact=True).click()
    page.get_by_label("Quantity", exact=True).fill("1000")
    page.get_by_role("button", name="Save").click()

    page.get_by_role("link", name="Add Goods Item").click()
    page.get_by_role("link", name="Section 5").first.click()
    page.get_by_role("textbox", name="---------").click()
    page.get_by_role(
        "option",
        name="5(1)(a) Any firearm capable of burst- or fully automatic fire and component parts of these.",
    ).click()
    page.get_by_label("No").check()
    page.get_by_label("Description").click()
    page.get_by_label("Description").fill("Section 5 Goods Unlimited")
    page.get_by_label("Unlimited Quantity").check()
    page.get_by_role("button", name="Save").click()

    # Section 5 - Obsolete Calibre
    page.get_by_role("link", name="Add Goods Item").click()
    page.get_by_role("link", name="Section 58(2) - Obsolete Calibre").click()
    page.locator("#id_curiosity_ornament").get_by_text("Yes").click()
    page.get_by_label("Do you acknowledge the above statement?").check()
    page.locator("#id_centrefire").get_by_text("Yes").click()
    page.locator("#id_manufacture").get_by_text("Yes").click()
    page.locator("#id_original_chambering").get_by_text("Yes").click()
    page.get_by_role("textbox", name="---------").click()
    page.get_by_role("option", name="9mm").click()
    page.get_by_label("Description").click()
    page.get_by_label("Description").fill("Section 5 Obsolete Goods")
    page.get_by_label("Quantity").click()
    page.get_by_label("Quantity").fill("54321")
    page.get_by_role("button", name="Save").click()

    # Section 5 - Other
    page.get_by_role("link", name="Add Goods Item").click()
    page.get_by_role("link", name="Section 58(2) - Other").click()
    page.locator("#id_curiosity_ornament_0").check()
    page.get_by_label("Do you acknowledge the above statement?").check()
    page.locator("#id_manufacture_0").check()
    page.get_by_label("Description").click()
    page.get_by_label("Description").fill("Section 5 Other Goods")
    page.get_by_label("Quantity").click()
    page.get_by_label("Quantity").fill("12345")
    page.locator("#id_muzzle_loading_0").check()
    page.locator("#id_rimfire").get_by_text("No").click()
    page.locator("#id_ignition").get_by_text("No").click()
    page.locator("#id_chamber").get_by_text("No").click()
    page.locator("#id_bore").get_by_text("No").click()
    page.get_by_role("button", name="Save").click()

    #
    # Add a certificate
    #
    page.get_by_role("link", name="Certificates").click()
    page.get_by_role("link", name="Add Certificate").click()
    page.get_by_label("Certificate Reference").click()
    page.get_by_label("Certificate Reference").fill("reference")
    page.get_by_role("combobox", name="Certificate Type").select_option("firearms")
    page.get_by_role("combobox", name="Constabulary").select_option("1")

    future_date = utils.get_future_datetime().date()
    issue_date = future_date.strftime(JQUERY_DATE_FORMAT)
    expiry_date = dt.date(future_date.year + 1, 1, 1).strftime(JQUERY_DATE_FORMAT)
    page.get_by_label("Date Issued").click()
    page.get_by_label("Date Issued").fill(issue_date)
    page.get_by_label("Date Issued").press("Enter")
    page.get_by_label("Expiry Date").click()
    page.get_by_label("Expiry Date").fill(expiry_date)
    page.get_by_label("Expiry Date").press("Enter")
    page.get_by_label("Document").set_input_files(sample_upload_file)
    page.get_by_role("button", name="Save").click()

    #
    # Add a section 5 authority
    #
    page.get_by_role("link", name="Add Section 5 Authority").click()
    page.get_by_label("Document").set_input_files(sample_upload_file)
    page.get_by_role("button", name="Save").click()

    #
    # Complete Details of Who Bought From section
    #
    page.get_by_role("link", name="Details of Who Bought From").click()
    page.get_by_label("Yes").check()
    page.get_by_text("Yes").click()
    page.get_by_role("button", name="Save").click()

    #
    # Add a Legal Person
    #
    page.get_by_role("link", name="Add Who Bought From (Legal Person)").click()
    page.get_by_label("Name of Legal Person").click()
    page.get_by_label("Name of Legal Person").fill("Legal person name")
    page.get_by_label("Registration Number").click()
    page.get_by_label("Registration Number").fill("Registration number")
    page.get_by_label("Street and Number").click()
    page.get_by_label("Street and Number").fill("1 street")
    page.get_by_label("Town/City").click()
    page.get_by_label("Town/City").fill("Town")
    page.get_by_label("Postcode").click()
    page.get_by_label("Postcode").fill("S112ZZ")  # /PS-IGNORE
    page.get_by_label("Region").click()
    page.get_by_label("Region").fill("Yorkshire")
    page.get_by_role("combobox", name="Country").select_option("1")
    page.get_by_role("combobox", name="Did you buy from a dealer?").select_option("yes")
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


def fa_sil_manage_and_complete_case(page: Page, app_id) -> None:
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
    page.get_by_role("combobox", name="Authority to possess covers items listed?").select_option(
        "n/a"
    )
    page.get_by_role(
        "combobox", name="Quantities listed within authority to possess restrictions?"
    ).select_option("yes")
    page.get_by_role("combobox", name="Authority to possess checked with police?").select_option(
        "no"
    )
    page.get_by_role("combobox", name="Case update required from applicant?").select_option("n/a")
    page.get_by_role("combobox", name="Further information request required?").select_option("yes")
    page.get_by_label(
        "Response Preparation - approve/refuse the request, edit details if necessary"
    ).check()
    page.get_by_role("combobox", name="Validity period correct?").select_option("yes")
    page.get_by_role(
        "combobox",
        name="Correct endorsements listed? Add/edit/remove as required (changes are automatically saved)",
    ).select_option("no")
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
    # Complete Response Preparation (Set Cover Letter)
    #
    page.get_by_role("link", name="Set Cover Letter").click()
    page.get_by_role("combobox", name="Template").select_option("79")
    page.get_by_role("button", name="Save").click()

    #
    # Complete Response Preparation (Licence Details)
    #
    page.locator('[data-test-id="edit-licence"]').click()
    utils.set_licence_end_date(page)

    page.get_by_role("combobox", name="Issue paper licence only?").select_option("false")
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
    page.get_by_role("button", name="Close this message").click()

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
