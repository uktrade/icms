import datetime as dt
from unittest.mock import MagicMock, create_autospec, patch

import pytest

from web.models import SILGoodsSection582Obsolete  # /PS-IGNORE
from web.models import SILGoodsSection582Other  # /PS-IGNORE
from web.models import SILGoodsSection1, SILGoodsSection2, SILGoodsSection5, Template
from web.types import DocumentTypes
from web.utils.pdf import utils


# TODO: Revisit when doing ICMSLST-1428
@pytest.fixture(autouse=True)
def mock_get_licence_endorsements(monkeypatch):
    mock_get_licence_endorsements = create_autospec(utils.get_licence_endorsements)
    mock_get_licence_endorsements.return_value = []
    monkeypatch.setattr(utils, "get_licence_endorsements", mock_get_licence_endorsements)


def test_fa_oil_get_preview_context(oil_app, licence, oil_expected_preview_context):
    actual_context = utils.get_fa_oil_licence_context(
        oil_app, licence, DocumentTypes.LICENCE_PREVIEW
    )
    oil_expected_preview_context["preview_licence"] = True
    oil_expected_preview_context["paper_licence_only"] = False
    oil_expected_preview_context["process"] = oil_app

    assert oil_expected_preview_context == actual_context


def test_fa_oil_setting_licence_dates(oil_app, licence, oil_expected_preview_context):
    licence.licence_start_date = dt.date(2022, 1, 1)
    licence.licence_end_date = dt.date(2025, 2, 21)

    oil_expected_preview_context["licence_start_date"] = "01 January 2022"
    oil_expected_preview_context["licence_end_date"] = "21 February 2025"
    oil_expected_preview_context["preview_licence"] = True
    oil_expected_preview_context["paper_licence_only"] = False
    oil_expected_preview_context["process"] = oil_app

    actual_context = utils.get_fa_oil_licence_context(
        oil_app, licence, DocumentTypes.LICENCE_PREVIEW
    )
    assert oil_expected_preview_context == actual_context


def test_fa_oil_office_eori_override_number(oil_app, licence, oil_expected_preview_context):
    oil_app.importer_office.eori_number = "GB_OVERRIDE"

    oil_expected_preview_context["eori_numbers"] = ["GB_OVERRIDE"]
    oil_expected_preview_context["preview_licence"] = True
    oil_expected_preview_context["paper_licence_only"] = False
    oil_expected_preview_context["process"] = oil_app

    actual_context = utils.get_fa_oil_licence_context(
        oil_app, licence, DocumentTypes.LICENCE_PREVIEW
    )
    assert oil_expected_preview_context == actual_context


def test_fa_oil_ni_office_postcode_returns_two_eori_numbers(
    oil_app, licence, oil_expected_preview_context
):
    oil_app.importer_office.postcode = "BT125QB"  # /PS-IGNORE

    oil_expected_preview_context["importer_postcode"] = "BT125QB"  # /PS-IGNORE
    oil_expected_preview_context["eori_numbers"] = ["GB123456789", "XI123456789"]
    oil_expected_preview_context["preview_licence"] = True
    oil_expected_preview_context["paper_licence_only"] = False
    oil_expected_preview_context["process"] = oil_app

    actual_context = utils.get_fa_oil_licence_context(
        oil_app, licence, DocumentTypes.LICENCE_PREVIEW
    )
    assert oil_expected_preview_context == actual_context


def test_fa_oil_ni_office_postcode_returns_two_override_eori_numbers(
    oil_app, licence, oil_expected_preview_context
):
    oil_app.importer_office.postcode = "BT125QB"  # /PS-IGNORE
    oil_app.importer_office.eori_number = "GB_OVERRIDE"

    oil_expected_preview_context["importer_postcode"] = "BT125QB"  # /PS-IGNORE
    oil_expected_preview_context["eori_numbers"] = ["GB_OVERRIDE", "XI_OVERRIDE"]
    oil_expected_preview_context["preview_licence"] = True
    oil_expected_preview_context["paper_licence_only"] = False
    oil_expected_preview_context["process"] = oil_app

    actual_context = utils.get_fa_oil_licence_context(
        oil_app, licence, DocumentTypes.LICENCE_PREVIEW
    )
    assert oil_expected_preview_context == actual_context


@patch("web.utils.pdf.utils._get_licence_number", return_value="0000001B")
def test_fa_oil_get_pre_sign_context(
    mock_get_licence, oil_app, licence, oil_expected_preview_context
):
    oil_expected_preview_context["licence_number"] = "0000001B"
    oil_expected_preview_context["preview_licence"] = False
    oil_expected_preview_context["paper_licence_only"] = False
    oil_expected_preview_context["process"] = oil_app

    actual_context = utils.get_fa_oil_licence_context(
        oil_app, licence, DocumentTypes.LICENCE_PRE_SIGN
    )
    assert oil_expected_preview_context == actual_context


@patch("web.utils.pdf.utils._get_fa_dfl_goods")
def test_fa_dfl_get_preview_context(mock_get_goods, dfl_app, licence, dfl_expected_preview_context):
    mock_get_goods.return_value = ["goods one", "goods two", "goods three"]

    dfl_expected_preview_context["goods"] = ["goods one", "goods two", "goods three"]
    dfl_expected_preview_context["preview_licence"] = True
    dfl_expected_preview_context["paper_licence_only"] = False
    dfl_expected_preview_context["process"] = dfl_app
    actual_context = utils.get_fa_dfl_licence_context(
        dfl_app, licence, DocumentTypes.LICENCE_PREVIEW
    )

    assert dfl_expected_preview_context == actual_context


@patch.multiple(
    "web.utils.pdf.utils",
    _get_fa_dfl_goods=MagicMock(return_value=["goods one", "goods two", "goods three"]),
    _get_licence_number=MagicMock(return_value="0000001B"),
)
def test_fa_dfl_get_pre_sign_context(dfl_app, licence, dfl_expected_preview_context, **mocks):
    dfl_expected_preview_context["goods"] = ["goods one", "goods two", "goods three"]
    dfl_expected_preview_context["licence_number"] = "0000001B"
    dfl_expected_preview_context["preview_licence"] = False
    dfl_expected_preview_context["paper_licence_only"] = False
    dfl_expected_preview_context["process"] = dfl_app

    actual_context = utils.get_fa_dfl_licence_context(
        dfl_app, licence, DocumentTypes.LICENCE_PRE_SIGN
    )
    assert dfl_expected_preview_context == actual_context


@pytest.mark.django_db
@patch("web.utils.pdf.utils._get_fa_sil_goods")
def test_fa_sil_get_preview_context(mock_get_goods, sil_app, licence, sil_expected_preview_context):
    mock_get_goods.return_value = [("goods one", 10), ("goods two", 20), ("goods three", 30)]

    sil_app.military_police = True
    template = Template.objects.get(template_code="FIREARMS_MARKINGS_NON_STANDARD")

    sil_expected_preview_context["goods"] = [
        ("goods one", 10),
        ("goods two", 20),
        ("goods three", 30),
    ]
    sil_expected_preview_context["preview_licence"] = True
    sil_expected_preview_context["paper_licence_only"] = False
    sil_expected_preview_context["process"] = sil_app
    sil_expected_preview_context["markings_text"] = template.template_content

    actual_context = utils.get_fa_sil_licence_context(
        sil_app, licence, DocumentTypes.LICENCE_PREVIEW
    )
    assert sil_expected_preview_context == actual_context


@pytest.mark.django_db
@patch.multiple(
    "web.utils.pdf.utils",
    _get_fa_sil_goods=MagicMock(
        return_value=[("goods one", 10), ("goods two", 20), ("goods three", 30)]
    ),
    _get_licence_number=MagicMock(return_value="0000001B"),
)
def test_fa_sil_get_pre_sign_context(sil_app, licence, sil_expected_preview_context, **mocks):
    sil_expected_preview_context["goods"] = [
        ("goods one", 10),
        ("goods two", 20),
        ("goods three", 30),
    ]
    sil_expected_preview_context["preview_licence"] = False
    sil_expected_preview_context["paper_licence_only"] = False
    sil_expected_preview_context["process"] = sil_app
    sil_expected_preview_context["licence_number"] = "0000001B"

    actual_context = utils.get_fa_sil_licence_context(
        sil_app, licence, DocumentTypes.LICENCE_PRE_SIGN
    )
    assert sil_expected_preview_context == actual_context


def test_section_1_get_fa_sil_goods_item():
    section_1_goods = [
        SILGoodsSection1(description="Goods 1", quantity=10),
        SILGoodsSection1(description="Goods 2", quantity=20),
    ]
    expected_goods = [("Goods 1 test suffix", 10), ("Goods 2 test suffix", 20)]
    actual_goods = utils.get_fa_sil_goods_item("goods_section1", section_1_goods, "test suffix")

    assert expected_goods == actual_goods


def test_section_2_get_fa_sil_goods_item():
    section_2_goods = [
        SILGoodsSection2(description="Goods 3", quantity=30),
        SILGoodsSection2(description="Goods 4", quantity=40),
    ]
    expected_goods = [("Goods 3 test suffix", 30), ("Goods 4 test suffix", 40)]
    actual_goods = utils.get_fa_sil_goods_item("goods_section2", section_2_goods, "test suffix")

    assert expected_goods == actual_goods


def test_section_5_get_fa_sil_goods_item():
    section_5_goods = [
        SILGoodsSection5(description="Goods 5", quantity=50),
        SILGoodsSection5(description="Goods 6", unlimited_quantity=True),
    ]

    expected_goods = [("Goods 5 test suffix", 50), ("Goods 6 test suffix", "Unlimited")]
    actual_goods = utils.get_fa_sil_goods_item("goods_section5", section_5_goods, "test suffix")

    assert expected_goods == actual_goods


def test_section_58_other_get_fa_sil_goods_item():
    section_58_other_goods = [
        SILGoodsSection582Other(description="Goods 7", quantity=70),  # /PS-IGNORE
        SILGoodsSection582Other(description="Goods 8", quantity=80),  # /PS-IGNORE
    ]

    expected_goods = [("Goods 7 test suffix", 70), ("Goods 8 test suffix", 80)]
    actual_goods = utils.get_fa_sil_goods_item(
        "goods_section582_others", section_58_other_goods, "test suffix"
    )

    assert expected_goods == actual_goods


def test_section_58_obsolete_get_fa_sil_goods_item():
    section_58_obsolete_goods = [
        SILGoodsSection582Obsolete(  # /PS-IGNORE
            description="Goods 9", quantity=90, obsolete_calibre="Calibre 1"
        ),
        SILGoodsSection582Obsolete(  # /PS-IGNORE
            description="Goods 10", quantity=100, obsolete_calibre="Calibre 2"
        ),
    ]

    expected_goods = [
        ("Goods 9 chambered in the obsolete calibre Calibre 1 test suffix", 90),
        ("Goods 10 chambered in the obsolete calibre Calibre 2 test suffix", 100),
    ]

    actual_goods = utils.get_fa_sil_goods_item(
        "goods_section582_obsoletes", section_58_obsolete_goods, "test suffix"
    )

    assert expected_goods == actual_goods


def test_invalid_section_returns_no_goods():
    expected_goods = []
    actual_goods = utils.get_fa_sil_goods_item("invalid_section", [], "test suffix")

    assert expected_goods == actual_goods


@pytest.mark.parametrize(
    "address,postcode,expected",
    [
        ("123\n\nTest", "123   345", "123 Test 123 345"),
        (" 123\nTest\n", "\nABC 345 ", "123 Test ABC 345"),
        (" 123\nTest\n", "", "123 Test"),
        (" 123\nTest\n", None, "123 Test"),
    ],
)
def test_clean_address(address, postcode, expected):
    assert utils.clean_address(address, postcode) == expected


@pytest.mark.parametrize(
    "date,expected",
    [
        (dt.date(2023, 1, 1), "1st January 2023"),
        (dt.date(2023, 2, 2), "2nd February 2023"),
        (dt.date(2023, 3, 3), "3rd March 2023"),
        (dt.date(2023, 4, 4), "4th April 2023"),
        (dt.date(2023, 5, 5), "5th May 2023"),
        (dt.date(2023, 6, 10), "10th June 2023"),
        (dt.date(2023, 7, 11), "11th July 2023"),
        (dt.date(2023, 8, 12), "12th August 2023"),
        (dt.date(2023, 9, 13), "13th September 2023"),
        (dt.date(2023, 10, 14), "14th October 2023"),
        (dt.date(2023, 11, 21), "21st November 2023"),
        (dt.date(2023, 12, 22), "22nd December 2023"),
        (dt.date(2024, 1, 23), "23rd January 2024"),
        (dt.date(2024, 2, 24), "24th February 2024"),
        (dt.date(2024, 3, 30), "30th March 2024"),
        (dt.date(2024, 5, 31), "31st May 2024"),
    ],
)
def test_day_ordinal_date(date, expected):
    assert utils.day_ordinal_date(date) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Some Text", ["Some Text"]),
        ("Some \nText", ["Some", "Text"]),
        ("\n\nSome\n\n \nText ", ["Some", "Text"]),
        ("\n\nSome\n\n\nMore\n\n\n\n   Text ", ["Some", "More", "Text"]),
        ("\n\nSome\n  \n  \nMore\n \n   \n \n   Text ", ["Some", "More", "Text"]),
    ],
)
def test_split_text_field_newlines(text, expected):
    assert utils.split_text_field_newlines(text) == expected
