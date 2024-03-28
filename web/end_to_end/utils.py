import datetime as dt
import re
from typing import Any, Optional

from playwright.sync_api import Locator, Page, expect

from web.forms.fields import JQUERY_DATE_FORMAT


def get_application_id(url: str, pattern: str, group_name: str = "app_pk") -> int:
    r"""Parse an application ID from a pattern.

    Example usage:
        >> dfl_id = utils.get_application_id(page.url, r"import/firearms/dfl/(?P<app_pk>\d+)/edit/")
    """

    match: Optional[re.Match] = re.search(re.compile(pattern), url)

    if not match:
        raise ValueError(f"Unable to find pattern {pattern!r} in url: {url}")

    return int(match.group(group_name))


def assert_page_url(page: Page, url_pattern: str) -> None:
    """Helper function to check a page url."""

    expected = re.compile(f".*{url_pattern}")

    expect(page).to_have_url(expected)


def get_future_datetime() -> dt.datetime:
    """Return a future datetime"""

    now = dt.datetime.now()

    return dt.datetime(year=now.year + 1, month=1, day=1, hour=15, minute=30)


def set_licence_end_date(page: Page) -> None:
    page.wait_for_load_state(state="domcontentloaded")
    future_date = get_future_datetime().date().strftime(JQUERY_DATE_FORMAT)
    page.get_by_label("Licence End Date").click()
    page.wait_for_load_state(state="domcontentloaded")
    page.get_by_label("Licence End Date").fill(future_date)
    page.get_by_role("button", name="Done").click()


def bypass_chief(page: Page, app_id: int) -> None:
    """Waiting for the Bypass CHIEF link is flaky as it's waiting for a task to complete."""

    click_or_wait_and_reload(
        page,
        locator_str=f'[data-test-id="workbasket-row-{app_id}"]',
        role_data={"role": "button", "name": "(TEST) Bypass CHIEF", "exact": True},
    )


def click_or_wait_and_reload(
    page: Page,
    locator_str: str,
    role_data: dict[str, Any] | None = None,
    timeout: int = 5000,
    attempts=5,
) -> None:
    """If an element is not on the page, wait and reload.
    Used for waiting for links that appear after asynchronous tasks"""
    if not role_data:
        return

    for _ in range(attempts):
        el = page.locator(locator_str).get_by_role(**role_data)
        if el.is_visible():
            el.click()
            return

        page.wait_for_timeout(timeout)
        page.reload()

    el = page.locator(locator_str).get_by_role(**role_data)
    el.click()


def get_wb_row(page: Page, app_id: int) -> Locator:
    return page.locator(f'[data-test-id="workbasket-row-{app_id}"]')


def get_search_row(page: Page, app_id: int) -> Locator:
    return page.locator(f'[data-test-id="search-results-row-{app_id}"]')


def get_cat_list_row(page: Page, cat_pk: int) -> Locator:
    return page.locator(f'[data-test-id="cat-results-row-{cat_pk}"]')


def get_cfs_product_list_row(page: Page, product_pk: int) -> Locator:
    return page.locator(f'[data-test-id="schedule-product-row-{product_pk}"]')
