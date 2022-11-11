from typing import TypedDict

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return browser_context_args | {"viewport": {"width": 1920, "height": 1080}}


@pytest.fixture(scope="session")
def browser(browser, browser_context_args):
    # Create a session for each user we can reuse later.
    system_users = ["importer_user", "exporter_user", "ilb_admin"]

    for username in system_users:
        context = browser.new_context(**browser_context_args)
        page: Page = context.new_page()

        # Go to base url
        page.goto("")
        page.get_by_label("Username").click()
        page.get_by_label("Username").fill(username)

        page.get_by_label("Password").click()
        page.get_by_label("Password").fill("admin")

        page.get_by_role("button", name="Sign in").click()
        expect(page).to_have_url("http://localhost:8080/workbasket/")

        context.storage_state(path=f"{username}.json")

        # Logged in and state stored so close the page.
        page.close()

    yield browser


@pytest.fixture()
def imp_page(browser, browser_context_args) -> Page:
    context = browser.new_context(storage_state="importer_user.json", **browser_context_args)
    page = context.new_page()

    page.goto("/workbasket/")

    _close_django_debug_toolbar(page)

    yield page


@pytest.fixture()
def exp_page(browser, browser_context_args) -> Page:
    context = browser.new_context(storage_state="exporter_user.json", **browser_context_args)
    page = context.new_page()

    page.goto("/workbasket/")

    _close_django_debug_toolbar(page)

    yield page


@pytest.fixture()
def ilb_page(browser, browser_context_args) -> Page:
    context = browser.new_context(storage_state="ilb_admin.json", **browser_context_args)
    page = context.new_page()

    page.goto("/workbasket/")

    _close_django_debug_toolbar(page)

    yield page


def _close_django_debug_toolbar(page):
    # Close the django debug toolbar if it is shown
    debug_toolbar = page.get_by_role("link", name="Hide »")

    if debug_toolbar.is_visible():
        debug_toolbar.click()


# Taken from the playwright api_structures file
class FilePayload(TypedDict):
    name: str
    mimeType: str
    buffer: bytes


@pytest.fixture()
def sample_upload_file() -> list[FilePayload]:
    return [{"name": "test.txt", "mimeType": "text/plain", "buffer": b"test"}]
