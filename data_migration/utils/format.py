from datetime import date, datetime
from typing import Any, Optional

from lxml import etree


def get_xml_val(xml: etree.ElementTree, xpath: str) -> Any:
    val_list = xml.xpath(xpath)

    if not val_list:
        return None

    return val_list[0]


def date_or_none(date_str: Optional[str]) -> Optional[date]:
    if not date_str:
        return None

    return datetime.strptime(date_str, "%Y-%m-%d").date()


def xml_str_or_none(xml: Optional[etree.ElementTree]) -> Optional[str]:
    if xml is None:
        return None

    xml_byte_str = etree.tostring(xml)
    return xml_byte_str.decode()


def str_to_bool(bool_str: Optional[str]) -> Optional[bool]:
    if bool_str and bool_str.lower() in ("y", "true"):
        return True
    elif bool_str and bool_str.lower() in ("n", "false"):
        return False

    return None


def str_to_yes_no(y_n_str: Optional[str]) -> Optional[str]:
    if y_n_str and y_n_str.lower() in ("y", "true"):
        return "yes"
    elif y_n_str and y_n_str.lower() in ("n", "false"):
        return "no"

    return None
