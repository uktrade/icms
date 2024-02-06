import datetime as dt
from unittest.mock import MagicMock, create_autospec, patch

import pytest

from web.models import SILGoodsSection582Obsolete  # /PS-IGNORE
from web.models import SILGoodsSection582Other  # /PS-IGNORE
from web.models import (
    EndorsementImportApplication,
    SILGoodsSection1,
    SILGoodsSection2,
    SILGoodsSection5,
    Template,
)
from web.types import DocumentTypes
from web.utils.pdf import utils


@pytest.fixture(autouse=True)
def mock_get_licence_endorsements(request, monkeypatch):
    """Mock get_licence_endorsements to avoid hitting the database."""

    # sometimes we want to test the real function, so we need to skip this fixture by marking the test
    if "no_mock_get_endorsements" in request.keywords:
        return
    else:
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

    oil_expected_preview_context["licence_start_date"] = "1st January 2022"
    oil_expected_preview_context["licence_end_date"] = "21st February 2025"
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
    oil_expected_preview_context["eori_numbers"] = ["GB1111111111ABCDE", "XI1111111111ABCDE"]
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
    assert utils._split_text_field_newlines(text) == expected


def test_cfs_cover_letter_key_filename():
    key, filename = utils.cfs_cover_letter_key_filename()
    assert filename == "CFS Letter.pdf"
    assert key == "static_documents/CFS Letter.pdf"


@pytest.mark.django_db
@pytest.mark.no_mock_get_endorsements
def test_collect_endorsements_empty(fa_sil_app_submitted):
    fa_sil_app_submitted.endorsements.all().delete()
    endorsements = utils.get_licence_endorsements(fa_sil_app_submitted)
    assert not endorsements


@pytest.mark.django_db
@pytest.mark.no_mock_get_endorsements
def test_collect_endorsements_normal(fa_sil_app_submitted):
    endorsements = utils.get_licence_endorsements(fa_sil_app_submitted)
    assert endorsements
    assert len(endorsements) == fa_sil_app_submitted.endorsements.count()
    assert endorsements[0][0] == fa_sil_app_submitted.endorsements.first().content


@pytest.mark.django_db
@pytest.mark.no_mock_get_endorsements
def test_collect_endorsements_split_newline_return_characters(fa_sil_app_submitted):
    EndorsementImportApplication.objects.create(
        import_application=fa_sil_app_submitted,
        content="This is a\r\ntest",
    )
    endorsements = utils.get_licence_endorsements(fa_sil_app_submitted)
    assert endorsements
    assert len(endorsements) == fa_sil_app_submitted.endorsements.count()
    assert len(endorsements[-1]) == 2
    assert endorsements[-1][0] == "This is a"
    assert endorsements[-1][1] == "test"
