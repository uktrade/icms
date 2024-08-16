import datetime as dt
import json

from web.tests.utils.pdf.test_visual_regression import date_created_json_file


def update_timestamp(file_name: str) -> None:
    """Update the timestamp for the benchmark PDF in the 'dates_created.json' file."""
    date_stamp_dict = json.loads(date_created_json_file.read_text())
    date_stamp_dict[file_name] = dt.datetime.now(dt.UTC).isoformat()
    date_created_json_file.write_text(json.dumps(date_stamp_dict, indent=4, sort_keys=True))
