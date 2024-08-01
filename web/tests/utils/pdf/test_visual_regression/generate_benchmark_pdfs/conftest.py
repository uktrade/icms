import json

import pytest

from web.tests.utils.pdf.test_visual_regression import date_created_json_file


@pytest.fixture(autouse=True, scope="session")
def save_timestamp():
    """Create a new 'dates_created.json' file so that we can store the time each benchmark PDF was created, so we can
    freeze time when generating the PDFs during test.

    We run this at the start of the session to ensure that the file is there."""

    if not date_created_json_file.exists():
        date_stamp_dict = {}
        date_created_json_file.write_text(json.dumps(date_stamp_dict, indent=4, sort_keys=True))
    yield
