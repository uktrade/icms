import datetime as dt
import re
import zoneinfo
from decimal import Decimal, InvalidOperation
from typing import Any

from django.core.exceptions import ValidationError
from django.core.validators import DecimalValidator
from django.utils import timezone
from lxml import etree

UK_TZ = zoneinfo.ZoneInfo("Europe/London")


def get_xml_val(xml: etree.ElementTree, xpath: str, text=True) -> Any:
    if text and not xpath.endswith("/text()"):
        xpath = xpath + "/text()"

    val_list = xml.xpath(xpath)

    if not val_list:
        return None

    val = val_list[0]

    if isinstance(val, str):
        return val.strip()

    return val


def date_or_none(date_str: str | None | dt.date | dt.datetime) -> dt.date | None:
    """Convert a date string into a date

    param date_str: A string of the date. Can come in a variety of formats

                    Examples: '14/10/24', '14/10/2024', '14-10-2024',
                              '14-10-24', '2024-10-14', '14 October 2024',
                              '14.10.24', '14.10.2024',
    """

    if not date_str:
        return None

    if isinstance(date_str, dt.datetime):
        return date_str.date()

    if isinstance(date_str, dt.date):
        return date_str

    if " " in date_str and len(date_str) > 10:
        return dt.datetime.strptime(date_str, "%d %B %Y").date()

    p_date_str = date_str.replace("/", "-").replace(".", "-")
    date_split = p_date_str.split("-")

    if len(date_split) > 3 or len(date_split[-1]) > 4:
        raise ValidationError(f"Date {date_str} not in parsable format")

    if len(date_split[0]) == 4:
        date_format = "%Y-%m-%d"
    elif len(date_split[-1]) == 4:
        date_format = "%d-%m-%Y"
    else:
        date_format = "%d-%m-%y"

    return dt.datetime.strptime(p_date_str, date_format).date()


def datetime_or_none(dt_str: str | None) -> dt.datetime | None:
    """Convert a datetime string to datetime

    :param dt_str: A string of the datetime. Example: 2022-07-25T11:05:59
    """

    if not dt_str:
        return None

    str_format = "%Y-%m-%dT%H:%M:%S"
    dt_val = dt.datetime.strptime(dt_str, str_format)

    return adjust_icms_v1_datetime(dt_val)


def adjust_icms_v1_datetime(dt_val: dt.datetime) -> dt.datetime:
    """Adjust an ICMS V1 naive datetime to an aware UTC datetime.

    Assumption: For ambiguous datetime values we are using the default fold of 0.
    E.g. We have no way of knowing if this `naive_dt` is GMT or BST
    >>> naive_dt = dt.datetime(2022, 10, 30, 1, 30, 0)
    >>> london = zoneinfo.ZoneInfo("Europe/London")
    >>> bst_val = naive_dt.replace(tzinfo=london, fold=0)
    >>> gmt_val = naive_dt.replace(tzinfo=london, fold=1)
    >>> print(bst_val)
        2022-10-30 01:30:00+01:00
    >>> print(gmt_val)
        2022-10-30 01:30:00+00:00
    >>> print(bst_val.astimezone(dt.timezone.utc))
        2022-10-30 00:30:00+00:00
    >>> print(gmt_val.astimezone(dt.timezone.utc))
        2022-10-30 01:30:00+00:00
    """

    if timezone.is_aware(dt_val):
        raise ValueError(f"Unable to adjust an aware datetime value: {dt_val}")

    # ICMS V1 datetime values are created using this:
    # https://docs.oracle.com/database/121/SQLRF/functions207.htm#SQLRF06124
    # Therefore replace the naive datetime with the correct timezone
    aware_dt = dt_val.replace(tzinfo=UK_TZ)

    # Return a datetime that has been offset to UTC
    utc_dt = aware_dt.astimezone(dt.timezone.utc)

    return utc_dt


def date_to_timezone(date: dt.date | None) -> dt.datetime | None:
    """Convert a date to a timezone aware datetime"""

    if not date:
        return None

    return dt.datetime.combine(date, dt.time.min, tzinfo=dt.timezone.utc)


def float_or_none(float_str: str | None) -> float | None:
    if not float_str:
        return None

    parsed = float(float_str)

    # Validate parsed is a number by trying to parse to int
    try:
        int(parsed)
    except ValueError:
        return None

    return parsed


def int_or_none(int_str: str | None) -> int | None:
    if not int_str:
        return None

    try:
        val = int(int_str)
    except ValueError:
        val = int(float(int_str))

    return val


def xml_str_or_none(xml: "etree.ElementTree | None") -> str | None:
    if xml is None:
        return None

    xml_byte_str = etree.tostring(xml)
    return xml_byte_str.decode().strip()


def str_to_bool(bool_str: str | None) -> bool | None:
    if bool_str and bool_str.lower() in ("y", "true"):
        return True

    if bool_str and bool_str.lower() in ("n", "false"):
        return False

    return None


def str_to_yes_no(y_n_str: str | None) -> str | None:
    if not y_n_str:
        return None

    y_n_str = y_n_str.lower()

    if y_n_str in ("y", "true"):
        return "yes"

    if y_n_str in ("n", "false"):
        return "no"

    if y_n_str in ("n/a", "na"):
        return "n/a"

    return None


def validate_decimal(
    fields: list[str], data: dict[str, Any], max_digits=9, decimal_places=2
) -> None:
    """Pops the field from the dictionary of data if it is not a valid decimal"""

    for field in fields:
        if data[field] is None:
            continue
        try:
            dv = DecimalValidator(max_digits, decimal_places)
            dv(
                Decimal(data[field]),
            )
        except InvalidOperation:
            data.pop(field)
        except ValueError:
            data.pop(field)
        except ValidationError:
            data.pop(field)


def validate_int(fields: list[str], data: dict[str, Any]) -> None:
    for field in fields:
        if data[field] is None:
            continue
        try:
            int(data[field])
        except ValueError:
            data.pop(field)


def split_address(address: str, prefix="address_", max_lines=5) -> dict[str, str]:
    """Splits an address by newline characters

    123 Test
    Test Town  --->  {"address_1": "123 Test", "address_2": "Test Town", "address_3": "Test City"}
    Test City
    """

    # TODO ICMSLST-1692: ILB to fix addresses which are more than 5 lines
    return {
        f"{prefix}{i}": address_line.strip()
        for i, address_line in enumerate(address.split("\n"), start=1)
        if address_line and address_line.strip() and i <= max_lines
    }


def str_to_list(list_str: str, delimiter: str = ";"):
    lst = [x for x in list_str.split(delimiter) if x]
    return lst or None


def extract_int_substr(int_str: str, substr: str) -> int | None:
    """Extract an integer from a string of kwargs

    username(WUA_ID=1, WUAH_ID=2) -> 1
    """

    match = re.search(f"({substr})\\d+", int_str)

    if not match:
        return None

    int_str = match[0].strip(substr)

    return int(int_str)


def extract_bracket_substr(bracket_str: str) -> str | None:
    """Extract text from paranthesis within a string

    Test User (testuser) -> testuser  /PS-IGNORE
    """

    match = re.search("\\((.*?)\\)", bracket_str)

    if not match:
        return None

    return match[1]
