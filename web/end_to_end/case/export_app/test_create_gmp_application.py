from playwright.sync_api import Page

from web.end_to_end import conftest, types, utils


def test_can_create_gmp(pages: conftest.UserPages, sample_upload_file: types.FilePayload) -> None:
    """End-to-end test for creating a GMP application.

    This tests requires multiple pages as there is a back and forth between user types.
    """

    with pages.exp_page() as exp_page:
        gmp_id = gmp_create(exp_page, sample_upload_file)

    with pages.ilb_page() as ilb_page:
        gmp_manage_and_complete_case(ilb_page, gmp_id)


def gmp_create(page: Page, sample_upload_file: types.FilePayload) -> int:
    page.get_by_role("link", name="New Certificate Application").click()

    page.get_by_role("link", name="Certificate of Good Manufacturing Practice").click()

    page.get_by_text("-- Select Exporter").click()
    page.get_by_role("option", name="Dummy exporter").click()
    page.get_by_role("combobox", name="-- Select Office").get_by_text("-- Select Office").click()
    page.get_by_role("option", name="Buckingham Palace\nLondon\nSW1A 1AA").click()  # /PS-IGNORE
    page.get_by_role("button", name="Create").click()

    gmp_id = utils.get_application_id(page.url, r"export/gmp/(?P<app_pk>\d+)/edit/")

    page.get_by_label("Name of the brand").click()
    page.get_by_label("Name of the brand").fill("A brand")

    page.locator("#id_is_responsible_person_0").check()
    page.locator("#id_responsible_person_name").click()
    page.locator("#id_responsible_person_name").fill("Responsible person name")
    page.locator("#id_responsible_person_postcode").click()
    page.locator("#id_responsible_person_postcode").fill("S19ZZ")  # /PS-IGNORE
    page.locator("#id_responsible_person_address").click()
    page.locator("#id_responsible_person_address").fill("Address")
    page.locator("#id_responsible_person_country_0").check()
    page.locator("#id_is_manufacturer_0").check()
    page.locator("#id_manufacturer_name").click()
    page.locator("#id_manufacturer_name").fill("Manufacturer name")
    page.locator("#id_manufacturer_postcode").click()
    page.locator("#id_manufacturer_postcode").fill("S12ZZ")  # /PS-IGNORE
    page.locator("#id_manufacturer_address").click()
    page.locator("#id_manufacturer_address").fill("Address")
    page.locator("#id_manufacturer_country_0").check()

    page.get_by_label("ISO 22716").check()
    page.locator("#id_auditor_accredited").get_by_text("Yes").click()
    page.locator("#id_auditor_certified").get_by_text("Yes").click()
    page.get_by_role("button", name="Save").click()
    page.get_by_role("link", name="Add ISO 22716 File").click()
    page.get_by_label("Document").set_input_files(sample_upload_file)
    page.get_by_role("button", name="Save").click()

    page.get_by_role("link", name="Add ISO 17021 File").click()
    page.get_by_label("Document").set_input_files(sample_upload_file)
    page.wait_for_timeout(100)
    page.get_by_role("button", name="Save").click()

    page.get_by_role("link", name="Add ISO 17065 File").click()
    page.get_by_label("Document").set_input_files(sample_upload_file)
    page.get_by_role("button", name="Save").click()

    page.get_by_role("link", name="Submit").click()
    page.get_by_label(
        'Confirm that you agree to the above by typing "I AGREE", in capitals, in this box'
    ).click()
    page.get_by_label(
        'Confirm that you agree to the above by typing "I AGREE", in capitals, in this box'
    ).fill("I AGREE")
    page.get_by_role("button", name="Submit Application").click()

    return gmp_id


def gmp_manage_and_complete_case(page: Page, gmp_id: int) -> None:
    #
    # Complete Take Ownership
    #
    workbasket_row = utils.get_wb_row(page, gmp_id)
    workbasket_row.get_by_role("button", name="Take Ownership").click()

    #
    # Click BEIS Emails to check it is available for GMP
    #
    page.get_by_role("link", name="BEIS Emails").click()

    #
    # Complete Response Preparation (Approve application)
    #
    page.get_by_role("link", name="Response Preparation").click()
    page.get_by_role("combobox", name="Decision").select_option("APPROVE")
    page.get_by_role("button", name="Save").click()

    #
    # Complete Authorisation
    #
    page.get_by_role("link", name="Authorisation").click()
    page.get_by_role("button", name="Start Authorisation (Close Case Processing)").click()

    workbasket_row = utils.get_wb_row(page, gmp_id)
    workbasket_row.get_by_role("link", name="Authorise Documents").click()
    page.get_by_role("button", name="Sign and Authorise").click()
    page.get_by_role("button", name="OK", exact=True).click()

    #
    # Close the popup: "Authorise Success: Application xxx/xxxx/xxxxx has been queued for document signing"
    #
    page.get_by_role("button", name="Close this message").click()
    page.get_by_role("link", name="Workbasket").click()
    utils.assert_page_url(page, "/workbasket/")

    #
    # Check application complete
    #
    workbasket_row = utils.get_wb_row(page, gmp_id)
    workbasket_row.get_by_role("cell", name="Completed ").is_visible()
