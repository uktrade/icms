import pytest
from playwright.sync_api import expect


@pytest.mark.end_to_end
def test_importer_access_workbasket(imp_page):
    page = imp_page
    user_link = page.get_by_role("link", name="Dave Jones (importer_user)")
    expect(user_link).to_be_visible()


@pytest.mark.end_to_end
def test_exporter_can_access_workbasket(exp_page):
    page = exp_page
    user_link = page.get_by_role("link", name="Sally Davis (exporter_user)")
    expect(user_link).to_be_visible()


@pytest.mark.end_to_end
def test_ilb_admin_can_access_workbasket(ilb_page):
    page = ilb_page
    user_link = page.get_by_role("link", name="Ashley Smith (ilb_admin)")
    expect(user_link).to_be_visible()
