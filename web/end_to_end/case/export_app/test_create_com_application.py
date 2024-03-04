from playwright.sync_api import Page

from web.end_to_end import conftest, utils


def test_can_create_com(pages: conftest.UserPages) -> None:
    """End-to-end test for creating a COM application.

    This tests requires multiple pages as there is a back and forth between user types.
    """

    with pages.exp_page() as exp_page:
        com_id = com_create(exp_page)

    with pages.ilb_page() as ilb_page:
        com_manage_and_complete_case(ilb_page, com_id)


def com_create(page: Page) -> int:
    page.get_by_role("link", name="New Certificate Application").click()

    page.get_by_role("link", name="Certificate of Manufacture").click()

    page.get_by_text("-- Select Exporter").click()
    page.get_by_role("option", name="Dummy exporter").click()
    page.get_by_role("combobox", name="-- Select Office").get_by_text("-- Select Office").click()
    page.get_by_role("option", name="Buckingham Palace\nLondon\nSW1A 1AA").click()  # /PS-IGNORE
    page.get_by_role("button", name="Create").click()

    com_id = utils.get_application_id(page.url, r"export/com/(?P<app_pk>\d+)/edit/")

    # This is the "Countries" select2 input
    page.get_by_role("searchbox").click()
    page.get_by_role("option", name="Afghanistan").click()
    page.get_by_role("searchbox").click()
    page.get_by_role("option", name="Albania").click()
    page.get_by_role("searchbox").click()
    page.get_by_role("option", name="Algeria").click()
    page.get_by_role("combobox", name="Is the pesticide on free sale in the UK?").select_option(
        "false"
    )
    page.get_by_role(
        "combobox", name="Is the applicant company the manufacturer of the pesticide?"
    ).select_option("true")
    page.get_by_label("Product name").click()
    page.get_by_label("Product name").fill("Product name value")
    page.get_by_label("Chemical name").click()
    page.get_by_label("Chemical name").fill("Chemical name value")
    page.get_by_label("Manufacturing process").click()
    page.get_by_label("Manufacturing process").fill("Manufacturing process value")
    page.get_by_role("button", name="Save").click()

    page.get_by_role("link", name="Submit").click()
    page.get_by_label(
        'Confirm that you agree to the above by typing "I AGREE", in capitals, in this box'
    ).click()
    page.get_by_label(
        'Confirm that you agree to the above by typing "I AGREE", in capitals, in this box'
    ).fill("I AGREE")
    page.get_by_role("button", name="Submit Application").click()

    return com_id


def com_manage_and_complete_case(page: Page, com_id: int) -> None:
    #
    # Complete Take Ownership
    #
    workbasket_row = utils.get_wb_row(page, com_id)
    workbasket_row.get_by_role("button", name="Take Ownership").click()

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

    #
    # Authorise Documents
    #
    workbasket_row = utils.get_wb_row(page, com_id)
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
    workbasket_row = utils.get_wb_row(page, com_id)
    workbasket_row.get_by_role("cell", name="Completed ").is_visible()
