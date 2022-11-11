import pytest
from playwright.sync_api import Page

from . import utils


@pytest.mark.end_to_end
def test_can_create_fa_dfl(imp_page: Page, sample_upload_file, base_url) -> None:
    page = imp_page

    page.get_by_role("link", name="New Import Application").click()
    utils.assert_page_url(page, base_url, "/import/")

    page.get_by_role("link", name="Deactivated Firearms Licence").click()
    utils.assert_page_url(page, base_url, "/import/create/firearms/dfl/")

    page.get_by_text("-- Select Importer").click()

    page.get_by_role("option", name="Dummy importer").click()

    page.get_by_role("combobox", name="-- Select Office").locator(
        'span[role="textbox"]:has-text("-- Select Office")'
    ).click()

    page.get_by_role(
        "option", name="3 Whitehall Pl\nWestminster\nLondon\nSW1A 2HP"  # /PS-IGNORE
    ).click()

    page.get_by_role("button", name="Create").click()

    dfl_id = utils.get_application_id(base_url, page.url)
    utils.assert_page_url(page, base_url, f"/import/firearms/dfl/{dfl_id}/edit/")

    page.get_by_label("Applicant's Reference", exact=False).click()

    page.get_by_label("Applicant's Reference", exact=False).fill("Reference")

    page.get_by_label("Proof Checked").check()

    page.get_by_role("combobox", name="Country Of Origin").select_option("19")

    page.get_by_role("combobox", name="Country Of Consignment").select_option("24")

    page.get_by_role("combobox", name="Constabulary").select_option("74")

    page.get_by_role("button", name="Save").click()
    utils.assert_page_url(page, base_url, f"/import/firearms/dfl/{dfl_id}/edit/")

    page.get_by_role("link", name="Add Goods").click()
    utils.assert_page_url(page, base_url, f"/import/firearms/dfl/{dfl_id}/goods-certificate/add/")

    page.get_by_label("Goods Description").click()

    page.get_by_label("Goods Description").fill("test")

    page.get_by_label("Deactivated Certificate Reference").click()

    page.get_by_label("Deactivated Certificate Reference").fill("test")

    page.get_by_role("combobox", name="Issuing Country").select_option("23")

    page.get_by_label("Document").set_input_files(sample_upload_file)

    page.get_by_role("button", name="Save").click()
    utils.assert_page_url(page, base_url, f"/import/firearms/dfl/{dfl_id}/edit/")

    page.get_by_role("link", name="Details of Who Bought From").click()
    utils.assert_page_url(page, base_url, f"/import/firearms/fa/{dfl_id}/import-contacts/manage/")

    page.locator("#id_know_bought_from").get_by_text("No").click()

    page.get_by_role("button", name="Save").click()
    utils.assert_page_url(page, base_url, f"/import/firearms/fa/{dfl_id}/import-contacts/manage/")

    page.get_by_role("link", name="Submit").click()
    utils.assert_page_url(page, base_url, f"/import/firearms/dfl/{dfl_id}/submit/")

    page.get_by_label(
        'Confirm that you agree to the above by typing "I AGREE", in capitals, in this box'
    ).click()
    page.get_by_label(
        'Confirm that you agree to the above by typing "I AGREE", in capitals, in this box'
    ).fill("I AGREE")

    page.get_by_role("button", name="Submit Application").click()
    utils.assert_page_url(page, base_url, "/workbasket/")
