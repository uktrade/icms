import datetime

from web.utils.pdf import types, utils


def test_get_fa_oil_preview_context(oil_app, oil_expected_preview_context):
    actual_context = utils.get_fa_oil_licence_context(oil_app, types.DocumentTypes.LICENCE_PREVIEW)

    assert oil_expected_preview_context == actual_context


def test_setting_licence_dates(oil_app, oil_expected_preview_context):
    oil_app.licence_start_date = datetime.date(2022, 1, 1)
    oil_app.licence_end_date = datetime.date(2025, 2, 21)

    oil_expected_preview_context["licence_start_date"] = "01 January 2022"
    oil_expected_preview_context["licence_end_date"] = "21 February 2025"

    actual_context = utils.get_fa_oil_licence_context(oil_app, types.DocumentTypes.LICENCE_PREVIEW)
    assert oil_expected_preview_context == actual_context


def test_office_eori_override_number(oil_app, oil_expected_preview_context):
    oil_app.importer_office.eori_number = "GB_OVERRIDE"

    oil_expected_preview_context["eori_numbers"] = ["GB_OVERRIDE"]

    actual_context = utils.get_fa_oil_licence_context(oil_app, types.DocumentTypes.LICENCE_PREVIEW)
    assert oil_expected_preview_context == actual_context


def test_ni_office_postcode_returns_two_eori_numbers(oil_app, oil_expected_preview_context):
    oil_app.importer_office.postcode = "BT125QB"  # /PS-IGNORE

    oil_expected_preview_context["importer_postcode"] = "BT125QB"  # /PS-IGNORE
    oil_expected_preview_context["eori_numbers"] = ["GB123456789", "XI123456789"]

    actual_context = utils.get_fa_oil_licence_context(oil_app, types.DocumentTypes.LICENCE_PREVIEW)
    assert oil_expected_preview_context == actual_context


def test_ni_office_postcode_returns_two_override_eori_numbers(
    oil_app, oil_expected_preview_context
):
    oil_app.importer_office.postcode = "BT125QB"  # /PS-IGNORE
    oil_app.importer_office.eori_number = "GB_OVERRIDE"

    oil_expected_preview_context["importer_postcode"] = "BT125QB"  # /PS-IGNORE
    oil_expected_preview_context["eori_numbers"] = ["GB_OVERRIDE", "XI_OVERRIDE"]

    actual_context = utils.get_fa_oil_licence_context(oil_app, types.DocumentTypes.LICENCE_PREVIEW)
    assert oil_expected_preview_context == actual_context
