from web.utils.validation import ApplicationErrors


def check_page_errors(errors: ApplicationErrors, page_name: str, error_field_names: list[str]):
    """Check if the supplied errors have the expected errors for the given page."""

    page_errors = errors.get_page_errors(page_name)

    assert page_errors is not None

    actual_error_names = sorted(e.field_name for e in page_errors.errors)

    assert sorted(error_field_names) == actual_error_names
