from playwright.sync_api import Page

from web.end_to_end import conftest, utils


def test_can_create_cfs(pages: conftest.UserPages) -> None:
    """End-to-end test for creating a CFS application.

    This tests requires multiple pages as there is a back and forth between user types.
    """

    with pages.exp_page() as exp_page:
        cfs_id = cfs_create(exp_page)

    with pages.ilb_page() as ilb_page:
        cfs_manage_and_complete_case(ilb_page, cfs_id)


def cfs_create(page: Page) -> int:
    page.get_by_role("link", name="New Certificate Application").click()
    page.get_by_role("link", name="Certificate of Free Sale").click()

    page.get_by_text("-- Select Exporter").click()
    page.get_by_role("option", name="Dummy exporter").click()
    page.get_by_role("combobox", name="-- Select Office").get_by_text("-- Select Office").click()

    page.get_by_role("option", name="Buckingham Palace\nLondon\nSW1A 1AA").click()  # /PS-IGNORE
    page.get_by_role("button", name="Create").click()
    page.get_by_placeholder("Select Country").click()
    page.get_by_role("option", name="Afghanistan").click()
    page.get_by_role("searchbox").click()
    page.get_by_role("option", name="Albania").click()
    page.get_by_role("button", name="Save").click()

    cfs_id = utils.get_application_id(page.url, r"export/cfs/(?P<app_pk>\d+)/edit/")

    # Edit the only schedule
    page.get_by_role("link", name="Edit").click()
    page.get_by_label("I am the manufacturer").check()
    page.locator("#id_brand_name_holder").get_by_text("Yes").click()
    page.get_by_placeholder("Select Legislation").click()
    page.get_by_role(
        "option", name="Aerosol Dispensers Regulations 2009/ 2824 as retained in UK law"
    ).click()
    page.get_by_label("The products are currently sold on the UK market").check()
    page.locator("#id_goods_placed_on_uk_market").get_by_text("Yes").click()
    page.locator("#id_goods_export_only").get_by_text("No").click()
    page.locator("#id_any_raw_materials").get_by_text("Yes").click()
    page.get_by_label("End Use or Final Product").click()
    page.get_by_label("End Use or Final Product").fill("End Use or Final Product value")
    page.get_by_role("combobox", name="Country Of Manufacture").select_option("1")
    page.get_by_text(
        "These products are manufactured in accordance with the Good Manufacturing Practi"
    ).click()
    page.get_by_role("button", name="Save").click()

    # Add a product to schedule 1
    page.get_by_role("link", name="Add Product").click()
    page.get_by_label("Product name").click()
    page.get_by_label("Product name").fill("Product 1")
    page.get_by_role("button", name="Save").click()

    # Navigagte back to main schedule view of application
    page.get_by_role("link", name="CFS Application").click()

    # Copy Schedule 1 (opens schedule 2)
    page.get_by_role("link", name="Copy").click()

    # Delete existing product
    page.get_by_role("button", name="Delete").click()

    # Change to Biocide regulation to change product page
    page.get_by_role(
        "listitem", name="Aerosol Dispensers Regulations 2009/ 2824 as retained in UK law"
    ).get_by_text("×").click()
    page.get_by_role(
        "option", name="Biocide Products Regulation 528/2012 as retained in UK law"
    ).click()
    page.get_by_role("button", name="Save").click()

    # Add a product to schedule 2
    page.get_by_role("link", name="Add Product").click()
    page.get_by_label("Product name").click()
    page.get_by_label("Product name").fill("Biocide Product")
    page.get_by_role("button", name="Save").click()

    page.get_by_role("link", name="Add PT Number").click()
    page.get_by_role("combobox", name="Product type number").select_option("1")
    page.get_by_role("button", name="Save").click()

    page.get_by_role("link", name="Add Active Ingredient").click()
    page.get_by_label("Name").click()
    page.get_by_label("Name").fill("name value")
    page.get_by_label("CAS Number").click()
    page.get_by_label("CAS Number").fill("11-11-1")
    page.get_by_role("button", name="Save").click()

    # Click save on the Goods list view
    page.get_by_role("button", name="Save").click()

    # Submit the application
    page.get_by_role("link", name="Submit").click()
    page.get_by_label(
        'Confirm that you agree to the above by typing "I AGREE", in capitals, in this box'
    ).click()
    page.get_by_label(
        'Confirm that you agree to the above by typing "I AGREE", in capitals, in this box'
    ).fill("I AGREE")
    page.get_by_role("button", name="Submit Application").click()

    return cfs_id


def cfs_manage_and_complete_case(page: Page, cfs_id: int) -> None:
    #
    # Complete Take Ownership
    #
    workbasket_row = utils.get_wb_row(page, cfs_id)
    workbasket_row.get_by_role("button", name="Take Ownership").click()

    #
    # Check HSE Emails is visible
    #
    page.get_by_role("link", name="HSE Emails").is_visible()

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
    workbasket_row = utils.get_wb_row(page, cfs_id)
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
    workbasket_row = utils.get_wb_row(page, cfs_id)
    workbasket_row.get_by_role("cell", name="Completed ").is_visible()
