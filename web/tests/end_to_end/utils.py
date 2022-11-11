from django.urls import resolve, resolvers
from playwright.sync_api import expect


def get_application_id(base_url: str, page_url: str, app_pk_kwarg: str = "application_pk") -> int:
    """Extract the application primary key from the supplied page url."""

    match: resolvers.ResolverMatch = resolve(page_url.replace(base_url, ""))

    return match.kwargs[app_pk_kwarg]


def assert_page_url(page, base_url, url: str) -> None:
    """Helper function to check a page url.

    Future version won't require base_url to be supplied.
    """

    expect(page).to_have_url(f"{base_url}{url}")
