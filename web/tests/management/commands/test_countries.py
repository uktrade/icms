import csv
import io
from unittest import mock

import pytest
from django.core.management import call_command

from web.management.commands.countries import read_country_csv, write_country_csv
from web.models import Country, CountryGroup


class TestReadCountryCSV:
    def test_read(self):
        rows = [
            ["first", "row", "is" "junk"],
            ["id", "name", "is_active", "type", "commission_code", "hmrc_code", "foo", "bar"],
            ["", "", "", "", "", "", "comment on foo", ""],
            ["a", "Mexico", "true", "X", "abc", "def", "Y", ""],
            ["b", "Canada", "false", "Y", "ghi", "jkl", "", "Y"],
        ]
        fh = io.StringIO()
        csv.writer(fh).writerows(rows)
        fh.seek(0)
        countries, groups = read_country_csv(fh)

        assert countries == [
            {
                "commission_code": "abc",
                "groups": ["foo"],
                "hmrc_code": "def",
                "id": "a",
                "is_active": "true",
                "name": "Mexico",
                "type": "X",
            },
            {
                "commission_code": "ghi",
                "groups": ["bar"],
                "hmrc_code": "jkl",
                "id": "b",
                "is_active": "false",
                "name": "Canada",
                "type": "Y",
            },
        ]
        assert groups == [
            {"name": "foo", "comments": "comment on foo"},
            {"name": "bar", "comments": ""},
        ]

    def test_read_headers_but_no_comments(self):
        rows = [
            ["id", "name", "is_active", "type", "commission_code", "hmrc_code", "foo"],
        ]
        fh = io.StringIO()
        csv.writer(fh).writerows(rows)
        fh.seek(0)
        countries, groups = read_country_csv(fh)

        assert countries == []
        assert groups == [{"name": "foo", "comments": ""}]

    def test_read_bad_csv_format(self):
        rows = [["foo", "bar", "baz"]]
        fh = io.StringIO()
        csv.writer(fh).writerows(rows)
        fh.seek(0)

        with pytest.raises(ValueError, match=r"Missing header, expected columns"):
            read_country_csv(fh)


class TestWriteCountryCSV:
    def test_write_column_header(self):
        fh = io.StringIO()
        countries = []
        groups = [CountryGroup(name="foo", comments="comment"), CountryGroup(name="bar")]
        write_country_csv(countries, groups, dest=fh)

        assert fh.getvalue() == (
            "id,name,is_active,type,commission_code,hmrc_code,bar,foo\r\n" ",,,,,,,comment\r\n"
        )

    @pytest.mark.django_db
    def test_write_group_membership(self):
        fh = io.StringIO()
        foo = Country.objects.create(name="Foo")
        bar = CountryGroup.objects.create(name="Bar")
        bar.countries.add(foo)

        write_country_csv([foo], [bar], dest=fh)

        assert fh.getvalue() == (
            f"id,name,is_active,type,commission_code,hmrc_code,Bar\r\n"
            f",,,,,,\r\n"
            f"{foo.pk},Foo,True,,,,Y\r\n"
        )


class TestManagementCommand:
    @pytest.mark.django_db
    def test_call_countries_export(self, capsys):
        # We have ~180 countries loaded as initial db migrations, but foreign
        # key constraints make it tedious to delete those. So let's just test
        # the CSV was written and has the column headers.
        call_command("countries", "export")
        captured = capsys.readouterr()
        first_row = next(csv.reader(io.StringIO(captured.out)))

        assert first_row[:6] == ["id", "name", "is_active", "type", "commission_code", "hmrc_code"]

    def test_call_countries_import(self, capsys):
        fh = io.StringIO("id,name,is_active,type,commission_code,hmrc_code,Bar\r\n")

        with mock.patch("sys.stdin", fh):
            call_command("countries", "import")

        captured = capsys.readouterr()

        assert "Summary: 1 groups, 0 countries" in captured.err
