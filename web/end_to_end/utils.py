import datetime as dt
import re
from typing import Optional

from playwright.sync_api import Locator, Page, expect


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


def get_wb_row(page: Page, app_id: int) -> Locator:
    return page.locator(f'[data-test-id="workbasket-row-{app_id}"]')


def get_search_row(page: Page, app_id: int) -> Locator:
    return page.locator(f'[data-test-id="search-results-row-{app_id}"]')
