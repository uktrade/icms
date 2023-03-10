import datetime as dt

import pytest
from django.forms import ValidationError
from django.utils import timezone
from lxml import etree

from data_migration.management.commands.utils.db import bulk_create, new_process_pk
from data_migration.management.commands.utils.format import format_name, format_row
from data_migration.models import Process
from data_migration.utils.format import (
    date_or_none,
    datetime_or_none,
    extract_int_substr,
    float_or_none,
    get_xml_val,
    int_or_none,
    reformat_placeholders,
    str_to_bool,
    str_to_list,
    str_to_yes_no,
    strip_foxid_attribute,
    validate_decimal,
    validate_int,
    xml_str_or_none,
)


@pytest.mark.parametrize(
    "name,expected", [("a_name", "A Name"), ("a name", "A name"), ("A Name", "A name")]
)
def test_format_name(name, expected):
    assert format_name(name) == expected


@pytest.mark.parametrize(
    "columns,row,includes,pk,expected",
    [
        (("a", "b", "c"), (1, 2, 3), None, None, {"a": 1, "b": 2, "c": 3}),
        (("a", "b", "c"), (1, 2, 3), ["b", "c"], None, {"b": 2, "c": 3}),
        (("a", "b", "c"), (1, 2, 3), None, 123, {"a": 1, "b": 2, "c": 3, "id": 123}),
    ],
)
def test_format_row(columns, row, includes, pk, expected):
    assert format_row(columns, row, includes, pk) == expected


def test_format_row_datetime():
    dt_val = dt.datetime.now()
    columns = ["a_datetime"]
    row = [dt_val]

    tz = timezone.make_aware(dt_val, dt.timezone.utc)

    assert format_row(columns, row) == {"a_datetime": tz}


@pytest.mark.django_db
def test_new_process_pk():
    assert new_process_pk() == 1
    obj = Process.objects.create(process_type="ABC", created=timezone.now())
    assert new_process_pk() == obj.pk + 1


@pytest.mark.django_db
def test_bulk_create():
    Process.objects.create(process_type="New", created=timezone.now())
    pk = new_process_pk()
    bulk_create(
        Process,
        [
            Process(process_type="ATest", id=pk, created=timezone.now()),
            Process(process_type="BTest", id=pk + 1, created=timezone.now()),
        ],
    )
    assert Process.objects.filter(id=pk, process_type="ATest").count() == 1
    assert Process.objects.filter(id=pk + 1, process_type="BTest").count() == 1
    obj = Process.objects.create(process_type="CTest", created=timezone.now())
    assert obj.pk == pk + 2


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (None, None),
        ("", None),
        (dt.date(2014, 10, 1), dt.date(2014, 10, 1)),
        (dt.datetime(2014, 10, 1), dt.date(2014, 10, 1)),
        ("2014-10-01", dt.date(2014, 10, 1)),
        ("01-10-2014", dt.date(2014, 10, 1)),
        ("01-10-14", dt.date(2014, 10, 1)),
        ("01/10/2014", dt.date(2014, 10, 1)),
        ("01/10/14", dt.date(2014, 10, 1)),
        ("01 October 2014", dt.date(2014, 10, 1)),
        ("01.10.2014", dt.date(2014, 10, 1)),
        ("01.10.14", dt.date(2014, 10, 1)),
    ],
)
def test_date_or_none(test_input, expected):
    assert date_or_none(test_input) == expected


def test_date_or_none_exception():
    with pytest.raises(ValidationError) as excinfo:
        date_or_none("2014-10-01T00:00:00")
    assert "Date 2014-10-01T00:00:00 not in parsable format" in str(excinfo.value)


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (None, None),
        ("", None),
        # datetime strings that were created in BST (UTC +1)
        ("2014-10-01T01:02:03", dt.datetime(2014, 10, 1, 0, 2, 3, tzinfo=dt.timezone.utc)),
        ("2022-10-12T12:22:21", dt.datetime(2022, 10, 12, 11, 22, 21, tzinfo=dt.timezone.utc)),
        ("2008-06-28T18:00:51", dt.datetime(2008, 6, 28, 17, 0, 51, tzinfo=dt.timezone.utc)),
        ("2022-10-30T01:30:00", dt.datetime(2022, 10, 30, 0, 30, 0, tzinfo=dt.timezone.utc)),
        # datetime strings that were created in GMT (Same as UTC)
        ("2022-11-02T08:33:11", dt.datetime(2022, 11, 2, 8, 33, 11, tzinfo=dt.timezone.utc)),
        ("2006-12-15T17:44:11", dt.datetime(2006, 12, 15, 17, 44, 11, tzinfo=dt.timezone.utc)),
        ("2015-02-28T14:56:11", dt.datetime(2015, 2, 28, 14, 56, 11, tzinfo=dt.timezone.utc)),
    ],
)
def test_datetime_or_none(test_input, expected):
    assert datetime_or_none(test_input) == expected


@pytest.mark.parametrize(
    "test,expected",
    [
        (None, None),
        ("", None),
        ("nan", None),
        ("1", 1),
        ("1.0", 1.0),
        ("1.1", 1.1),
        ("1.11", 1.11),
    ],
)
def test_float_or_none(test, expected):
    assert float_or_none(test) == expected


@pytest.mark.parametrize(
    "int_str,expected",
    [
        (None, None),
        ("", None),
        ("1", 1),
        ("1.0", 1),
    ],
)
def test_int_or_none(int_str, expected):
    assert int_or_none(int_str) == expected


@pytest.mark.parametrize(
    "xml_str,xpath,expected",
    [
        ("<ROOT><A>a</A><B>b</B></ROOT>", "/ROOT/A/text()", "a"),
        ("<ROOT><A>a</A><B>b</B></ROOT>", "//A", "a"),
        ("<ROOT><A>a</A><B>b</B></ROOT>", "./A/text()", "a"),
        ("<ROOT><A>a</A><B> b\n</B></ROOT>", "/ROOT/B", "b"),
        ("<ROOT><A>a</A><B> b </B></ROOT>", "ROOT/C/text()", None),
    ],
)
def test_get_xml_val(xml_str, xpath, expected):
    xml = etree.fromstring(xml_str)
    assert expected == get_xml_val(xml, xpath)


@pytest.mark.parametrize(
    "xml_str",
    [
        ("<ROOT><A>a</A><B>b</B></ROOT>"),
        ("\n<ROOT><A>a</A><B>b</B></ROOT> "),
        (None),
    ],
)
def test_xml_str_or_none(xml_str):
    if xml_str:
        xml = etree.fromstring(xml_str)
        assert xml_str.strip() == xml_str_or_none(xml)
    else:
        assert xml_str_or_none(xml_str) is None


@pytest.mark.parametrize(
    "bool_str,expected",
    [
        ("Y", True),
        ("N", False),
        ("y", True),
        ("n", False),
        ("TRUE", True),
        ("true", True),
        ("FALSE", False),
        ("false", False),
        ("", None),
        (None, None),
    ],
)
def test_str_to_bool(bool_str, expected):
    assert str_to_bool(bool_str) is expected


@pytest.mark.parametrize(
    "y_n_str,expected",
    [
        ("Y", "yes"),
        ("N", "no"),
        ("y", "yes"),
        ("n", "no"),
        ("TRUE", "yes"),
        ("true", "yes"),
        ("FALSE", "no"),
        ("false", "no"),
        ("N/A", "n/a"),
        ("NA", "n/a"),
        ("n/a", "n/a"),
        ("na", "n/a"),
        ("", None),
        (None, None),
    ],
)
def test_str_to_yes_no(y_n_str, expected):
    assert str_to_yes_no(y_n_str) == expected


@pytest.mark.parametrize(
    "fields,data,expected",
    [
        (["a"], {"a": "1.2", "b": "1.2a"}, {"a": "1.2", "b": "1.2a"}),
        (["b"], {"a": "1.2", "b": "1.2a"}, {"a": "1.2"}),
        (["a", "b"], {"a": "1", "b": "1.2a"}, {"a": "1"}),
        (["a", "b"], {"a": "11111111111", "b": "1.23412"}, {}),
        (["a"], {"a": None, "b": "1.2a"}, {"a": None, "b": "1.2a"}),
    ],
)
def test_validate_decimal(fields, data, expected):
    validate_decimal(fields, data)
    assert data == expected


@pytest.mark.parametrize(
    "fields,data,expected",
    [
        (["a"], {"a": "12", "b": "1.2a"}, {"a": "12", "b": "1.2a"}),
        (["b"], {"a": "1.2", "b": "1.2a"}, {"a": "1.2"}),
        (["a", "b"], {"a": "1", "b": "1.2a"}, {"a": "1"}),
        (["a", "b"], {"a": "11111111111", "b": "1.23412"}, {"a": "11111111111"}),
        (["a"], {"a": None, "b": "1.2a"}, {"a": None, "b": "1.2a"}),
    ],
)
def test_validate_int(fields, data, expected):
    validate_int(fields, data)
    assert data == expected


def test_str_to_list():
    assert str_to_list("a;b;c") == ["a", "b", "c"]
    assert str_to_list("a/b/c", "/") == ["a", "b", "c"]
    assert str_to_list("a;;b;c;;") == ["a", "b", "c"]
    assert str_to_list("") is None


@pytest.mark.parametrize(
    "int_str,substr,expected",
    [
        ("abc=1, fg=2", "abc=", 1),
        ("abc=1, fg=2", "fg=", 2),
        ("abc=1, fg=2", "h=", None),
    ],
)
def test_extract_int_substr(int_str, substr, expected):
    assert extract_int_substr(int_str, substr) == expected


@pytest.mark.parametrize(
    "content,expected",
    [
        ("<p>test</p>", "<p>test</p>"),
        ('<p attr="1234">test</p>', '<p attr="1234">test</p>'),
        ('<p foxid="1234_abc">test</p>', "<p>test</p>"),  # /PS-IGNORE
        ('<p foxid="abc_123" attr="1234">test</p>', '<p attr="1234">test</p>'),  # /PS-IGNORE
        (
            '<p foxid="7fh32_fwef">test</p><p foxid="23123_dasada">test</p>',
            "<p>test</p><p>test</p>",
        ),  # /PS-IGNORE
    ],
)
def test_strip_foxid_attribute(content, expected):
    assert strip_foxid_attribute(content) == expected


def test_reformat_placeholders():
    content = "<MM>ABC</MM> more text <MM>def</MM>"
    expected = "[[ABC]] more text [[def]]"

    assert reformat_placeholders(content) == expected
