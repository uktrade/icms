from contextlib import contextmanager

import pytest
from playwright.sync_api import Page, expect

from . import types


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


class UserPages:
    """Class to manage using multiple pages in a test."""

    def __init__(self, browser, browser_context_args):
        self.browser = browser
        self.browser_context_args = browser_context_args

    @contextmanager
    def imp_page(self):
        """Return a page logged in as an importer viewing the workbasket."""

        page = self._get_page("importer_user.json")

        yield page

        page.close()

    @contextmanager
    def exp_page(self):
        """Return a page logged in as an exporter viewing the workbasket."""

        page = self._get_page("exporter_user.json")

        yield page

        page.close()

    @contextmanager
    def ilb_page(self):
        """Return a page logged in as an ILB admin viewing the workbasket."""

        page = self._get_page("ilb_admin.json")

        yield page

        page.close()

    def _get_page(self, storage_state: str) -> Page:
        context = self.browser.new_context(storage_state=storage_state, **self.browser_context_args)
        page = context.new_page()

        page.goto("/workbasket/")

        _close_django_debug_toolbar(page)

        return page


@pytest.fixture(scope="session")
def pages(browser, browser_context_args) -> UserPages:
    return UserPages(browser, browser_context_args)


@pytest.fixture()
def imp_page(users) -> Page:
    with users.imp_page() as page:
        yield page


@pytest.fixture()
def exp_page(users) -> Page:
    with users.exp_page() as page:
        yield page


@pytest.fixture()
def ilb_page(users) -> Page:
    with users.ilb_page() as page:
        yield page


def _close_django_debug_toolbar(page: Page) -> None:
    # Close the django debug toolbar if it is shown
    debug_toolbar = page.get_by_role("link", name="Hide »")

    if debug_toolbar.is_visible():
        debug_toolbar.click()


@pytest.fixture()
def sample_upload_file() -> list[types.FilePayload]:
    return [{"name": "test.txt", "mimeType": "text/plain", "buffer": b"test"}]
