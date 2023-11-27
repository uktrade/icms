from playwright.sync_api import Page, expect


def test_importer_access_workbasket(imp_page: Page) -> None:
    page = imp_page
    user_link = page.get_by_role("link", name="Dave Jones")
    expect(user_link).to_be_visible()


def test_exporter_can_access_workbasket(exp_page: Page) -> None:
    page = exp_page
    user_link = page.get_by_role("link", name="Sally Davis")
    expect(user_link).to_be_visible()


def test_ilb_admin_can_access_workbasket(ilb_page: Page) -> None:
    page = ilb_page
    user_link = page.get_by_role("link", name="Ashley Smith")
    expect(user_link).to_be_visible()
