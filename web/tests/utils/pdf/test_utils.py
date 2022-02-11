import datetime
from unittest.mock import patch

from web.utils.pdf import types, utils


def test_fa_oil_get_preview_context(oil_app, oil_expected_preview_context):
    actual_context = utils.get_fa_oil_licence_context(oil_app, types.DocumentTypes.LICENCE_PREVIEW)

    assert oil_expected_preview_context == actual_context


def test_fa_oil_setting_licence_dates(oil_app, oil_expected_preview_context):
    oil_app.licence_start_date = datetime.date(2022, 1, 1)
    oil_app.licence_end_date = datetime.date(2025, 2, 21)

    oil_expected_preview_context["licence_start_date"] = "01 January 2022"
    oil_expected_preview_context["licence_end_date"] = "21 February 2025"

    actual_context = utils.get_fa_oil_licence_context(oil_app, types.DocumentTypes.LICENCE_PREVIEW)
    assert oil_expected_preview_context == actual_context


def test_fa_oil_office_eori_override_number(oil_app, oil_expected_preview_context):
    oil_app.importer_office.eori_number = "GB_OVERRIDE"

    oil_expected_preview_context["eori_numbers"] = ["GB_OVERRIDE"]

    actual_context = utils.get_fa_oil_licence_context(oil_app, types.DocumentTypes.LICENCE_PREVIEW)
    assert oil_expected_preview_context == actual_context


def test_fa_oil_ni_office_postcode_returns_two_eori_numbers(oil_app, oil_expected_preview_context):
    oil_app.importer_office.postcode = "BT125QB"  # /PS-IGNORE

    oil_expected_preview_context["importer_postcode"] = "BT125QB"  # /PS-IGNORE
    oil_expected_preview_context["eori_numbers"] = ["GB123456789", "XI123456789"]

    actual_context = utils.get_fa_oil_licence_context(oil_app, types.DocumentTypes.LICENCE_PREVIEW)
    assert oil_expected_preview_context == actual_context


def test_fa_oil_ni_office_postcode_returns_two_override_eori_numbers(
    oil_app, oil_expected_preview_context
):
    oil_app.importer_office.postcode = "BT125QB"  # /PS-IGNORE
    oil_app.importer_office.eori_number = "GB_OVERRIDE"

    oil_expected_preview_context["importer_postcode"] = "BT125QB"  # /PS-IGNORE
    oil_expected_preview_context["eori_numbers"] = ["GB_OVERRIDE", "XI_OVERRIDE"]

    actual_context = utils.get_fa_oil_licence_context(oil_app, types.DocumentTypes.LICENCE_PREVIEW)
    assert oil_expected_preview_context == actual_context


def test_fa_oil_get_pre_sign_context(oil_app, oil_expected_preview_context):
    oil_expected_preview_context["licence_number"] = "ICMSLST-1224: Real Licence Number"

    actual_context = utils.get_fa_oil_licence_context(oil_app, types.DocumentTypes.LICENCE_PRE_SIGN)
    assert oil_expected_preview_context == actual_context


@patch("web.utils.pdf.utils._get_fa_dfl_goods")
def test_fa_dfl_get_preview_context(mock_get_goods, dfl_app, dfl_expected_preview_context):
    mock_get_goods.return_value = ["goods one", "goods two", "goods three"]

    dfl_expected_preview_context["goods"] = ["goods one", "goods two", "goods three"]
    actual_context = utils.get_fa_dfl_licence_context(dfl_app, types.DocumentTypes.LICENCE_PREVIEW)

    assert dfl_expected_preview_context == actual_context


@patch("web.utils.pdf.utils._get_fa_dfl_goods")
def test_fa_dfl_get_pre_sign_context(mock_get_goods, dfl_app, dfl_expected_preview_context):
    mock_get_goods.return_value = ["goods one", "goods two", "goods three"]

    dfl_expected_preview_context["goods"] = ["goods one", "goods two", "goods three"]
    dfl_expected_preview_context["licence_number"] = "ICMSLST-1224: Real Licence Number"

    actual_context = utils.get_fa_dfl_licence_context(dfl_app, types.DocumentTypes.LICENCE_PRE_SIGN)
    assert dfl_expected_preview_context == actual_context
