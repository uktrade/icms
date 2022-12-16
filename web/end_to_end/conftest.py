import logging
import os
import pathlib
from contextlib import contextmanager
from typing import Any, Dict, Generator, List

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Request, Response

from . import types, utils

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: Dict[str, Any]) -> Dict[str, Any]:
    return {**browser_context_args, "viewport": {"width": 1920, "height": 1080}}


class UserPages:
    """Class to manage using multiple pages in a test."""

    def __init__(self, browser: Browser, browser_context_args: Dict[str, Any]) -> None:
        self.browser = browser
        self.browser_context_args = browser_context_args

    @contextmanager
    def imp_page(self) -> Generator[Page, None, None]:
        """Return a page logged in as an importer viewing the workbasket."""

        page = self._get_page("importer_user.json")
        debug_page(page)

        yield page

        page.close()

    @contextmanager
    def exp_page(self) -> Generator[Page, None, None]:
        """Return a page logged in as an exporter viewing the workbasket."""

        page = self._get_page("exporter_user.json")
        debug_page(page)

        yield page

        page.close()

    @contextmanager
    def ilb_page(self) -> Generator[Page, None, None]:
        """Return a page logged in as an ILB admin viewing the workbasket."""

        page = self._get_page("ilb_admin.json")
        debug_page(page)

        yield page

        page.close()

    def _get_page(self, storage_state: str) -> Page:
        if not pathlib.Path(storage_state).exists():
            logger.info("Creating storage state: %s", storage_state)
            self._login_user(storage_state)

        logger.info("Creating context from storage state: %s", storage_state)
        context: BrowserContext = self.browser.new_context(
            storage_state=storage_state, **self.browser_context_args
        )

        # Timeout in ms
        context.set_default_timeout(5_000)

        page = context.new_page()
        page.goto("/workbasket/")

        _close_django_debug_toolbar(page)

        return page

    def _login_user(self, storage_state: str, user_password: str = "admin") -> None:
        username = storage_state.replace(".json", "")

        logger.info("Logging in the following user: %s", username)

        context: BrowserContext = self.browser.new_context(**self.browser_context_args)
        page: Page = context.new_page()

        # Go to base url
        page.goto("")
        page.get_by_label("Username").click()
        page.get_by_label("Username").fill(username)

        page.get_by_label("Password").click()
        page.get_by_label("Password").fill(user_password)

        page.get_by_role("button", name="Sign in").click()
        utils.assert_page_url(page, "/workbasket/")

        context.storage_state(path=f"{username}.json")

        # Logged in and state stored so close the page.
        page.close()


def debug_page(page: Page) -> None:
    """Add to a page for debugging an error"""
    page.on("request", on_request)
    page.on("response", on_response)


@pytest.fixture()
def pages(browser: Browser, browser_context_args: Dict[str, Any]) -> UserPages:
    return UserPages(browser, browser_context_args)


@pytest.fixture()
def imp_page(pages: UserPages) -> Generator[Page, None, None]:
    with pages.imp_page() as page:
        debug_page(page)

        yield page


@pytest.fixture()
def exp_page(pages: UserPages) -> Generator[Page, None, None]:
    with pages.exp_page() as page:
        debug_page(page)

        yield page


@pytest.fixture()
def ilb_page(pages: UserPages) -> Generator[Page, None, None]:
    with pages.ilb_page() as page:
        debug_page(page)

        yield page


def _close_django_debug_toolbar(page: Page) -> None:
    # Close the django debug toolbar if it is shown
    debug_toolbar = page.get_by_role("link", name="Hide »")

    if debug_toolbar.is_visible():
        debug_toolbar.click()


@pytest.fixture()
def sample_upload_file() -> List[types.FilePayload]:
    return [{"name": "test.txt", "mimeType": "text/plain", "buffer": b"test"}]


def on_request(r: Request) -> None:
    # Ignore static links
    if "/static/" in r.url:
        return

    current_test = _get_test_name()

    logger.info("- %s >> %s - %s - %s", current_test, r.method, r.url, r.post_data_json)


def on_response(r: Response) -> None:
    # Ignore static links
    if "/static/" in r.url:
        return

    current_test = _get_test_name()

    logger.info("- %s << %s - %s", current_test, r.status, r.url)


def _get_test_name() -> str:
    """Get the current test name.

    Converts this: test_create_fa_dfl_application.py::test_can_create_fa_dfl[chromium] (call)
    to this: "test_can_create_fa_dfl"
    """

    # The format of this can change when upgrading pytest
    # https://docs.pytest.org/en/7.1.x/example/simple.html#pytest-current-test-environment-variable
    current_test = os.environ.get("PYTEST_CURRENT_TEST", "")

    return current_test.split("::")[-1].split("[")[0]
