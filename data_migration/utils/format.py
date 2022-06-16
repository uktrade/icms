from datetime import date, datetime
from typing import Any, Optional

from django.forms import ValidationError
from lxml import etree


def get_xml_val(xml: etree.ElementTree, xpath: str) -> Any:
    val_list = xml.xpath(xpath)

    if not val_list:
        return None

    val = val_list[0]

    if isinstance(val, str):
        return val.strip()

    return val


def date_or_none(date_str: Optional[str]) -> Optional[date]:
    """Convert a date string into a date

    :param date_str: A string of the date. Can come in a variety of formats

                    Examples: '14/10/24', '14/10/2024', '14-10-2024',
                              '14-10-24', '2024-10-14', '14 October 2024'
    """

    if not date_str:
        return None

    if " " in date_str and len(date_str) > 10:
        return datetime.strptime(date_str, "%d %B %Y").date()

    p_date_str = date_str.replace("/", "-")
    date_split = p_date_str.split("-")

    if len(date_split) > 3 or len(date_split[-1]) > 4:
        raise ValidationError(f"Date {date_str} not in parsable format")

    if len(date_split[0]) == 4:
        date_format = "%Y-%m-%d"
    elif len(date_split[-1]) == 4:
        date_format = "%d-%m-%Y"
    else:
        date_format = "%d-%m-%y"

    return datetime.strptime(p_date_str, date_format).date()


def float_or_none(float_str: Optional[str]) -> Optional[float]:
    if not float_str:
        return None

    parsed = float(float_str)

    # Validate parsed is a number by trying to parse to int
    try:
        int(parsed)
    except ValueError:
        return None

    return parsed


def int_or_none(int_str: Optional[str]) -> Optional[int]:
    if not int_str:
        return None

    return int(int_str)


def xml_str_or_none(xml: Optional[etree.ElementTree]) -> Optional[str]:
    if xml is None:
        return None

    xml_byte_str = etree.tostring(xml)
    return xml_byte_str.decode().strip()


def str_to_bool(bool_str: Optional[str]) -> Optional[bool]:
    if bool_str and bool_str.lower() in ("y", "true"):
        return True

    if bool_str and bool_str.lower() in ("n", "false"):
        return False

    return None


def str_to_yes_no(y_n_str: Optional[str]) -> Optional[str]:
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
