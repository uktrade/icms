import datetime as dt

import pytest
from django.conf import settings

from web.domains.template.context import (
    ScheduleParagraphContext,
    UserManagementContext,
    _get_import_goods_description,
    _get_sil_goods_text,
)
from web.sites import get_exporter_site_domain, get_importer_site_domain


def test_get_sil_section_1_goods_text():
    assert _get_sil_goods_text("1", "20", "some description", None) == (
        "20 x some description to which Section 1 of the Firearms Act 1968, as amended, applies."
    )


def test_get_sil_section_5_unlimited_goods_text():
    assert _get_sil_goods_text("5", None, "another description", None) == (
        "another description to which Section 5 of the Firearms Act 1968, as amended, applies."
    )


def test_get_sil_section_5_obs_goods_text():
    assert _get_sil_goods_text("58(2)", "11", "test", "100 bore") == (
        "11 x test chambered in the obsolete calibre 100 bore"
        " to which Section 58(2) of the Firearms Act 1968, as amended, applies."
    )


def test_get_import_goods_description_dfl(fa_dfl_app_submitted):
    assert _get_import_goods_description(fa_dfl_app_submitted) == "goods_description value"


def test_get_import_goods_description_oil(fa_oil_app_submitted):
    assert _get_import_goods_description(fa_oil_app_submitted) == (
        "Firearms, component parts thereof, or ammunition of any applicable"
        " commodity code, other than those falling under Section 5 of the Firearms Act 1968 as amended."
    )


def test_get_import_goods_description_sil(fa_sil_app_submitted):
    assert _get_import_goods_description(fa_sil_app_submitted) == (
        "111 x Section 1 goods to which Section 1 of the Firearms Act 1968, as amended, applies.\n"
        "222 x Section 2 goods to which Section 2 of the Firearms Act 1968, as amended, applies.\n"
        "333 x Section 5 goods to which Section 5(A) section 5 subsection of the Firearms Act 1968, as amended, applies.\n"
        "444 x Section 58 obsoletes goods chambered in the obsolete calibre Obsolete calibre value to which "
        "Section 58(2) of the Firearms Act 1968, as amended, applies.\n"
        "555 x Section 58 other goods to which Section 58(2) of the Firearms Act 1968, as amended, applies."
    )


def test_get_import_goods_description_sanctions(sanctions_app_submitted):
    assert _get_import_goods_description(sanctions_app_submitted) == (
        "1000 x Test Goods\n56.78 x More Commoditites"
    )


def test_get_import_goods_description_wood(wood_app_submitted):
    with pytest.raises(
        ValueError,
        match=r"GOODS_DESCRIPTION placeholder not supported for process type WoodQuotaApplication",
    ):
        _get_import_goods_description(wood_app_submitted)


def test_schedule_paragraph_context(cfs_app_submitted):
    schedule = cfs_app_submitted.schedules.first()
    context = ScheduleParagraphContext(schedule)
    address = "E1 ADDRESS LINE 1 E1 ADDRESS LINE 2 HG15DB"  # /PS-IGNORE

    assert context["EXPORTER_NAME"] == "TEST EXPORTER 1"
    assert context["EXPORTER_ADDRESS_FLAT"] == address
    assert context["COUNTRY_OF_MANUFACTURE"] == "Afghanistan"

    with pytest.raises(
        ValueError,
        match=r"RANDOM_VALUE is not a valid schedule paragraph context value",
    ):
        context["RANDOM_VALUE"]


def test_importer_user_management_context(importer_one_contact):
    importer_one_contact.importer_last_login = dt.datetime(2021, 10, 1, 12, 1, 1)
    context = UserManagementContext(importer_one_contact)
    assert context["PLATFORM"] == "Apply for an import licence"
    assert context["CASE_OFFICER_EMAIL"] == settings.ILB_CONTACT_EMAIL
    assert context["PLATFORM_LINK"] == get_importer_site_domain()
    with pytest.raises(
        ValueError,
        match=r"RANDOM_VALUE is not a valid user management template context value",
    ):
        context["RANDOM_VALUE"]


def test_exporter_user_management_context(exporter_one_contact):
    exporter_one_contact.exporter_last_login = dt.datetime(2021, 10, 1, 12, 1, 1)
    context = UserManagementContext(exporter_one_contact)
    assert context["PLATFORM"] == "Apply for an export certificate"
    assert context["CASE_OFFICER_EMAIL"] == settings.ILB_CONTACT_EMAIL
    assert context["PLATFORM_LINK"] == get_exporter_site_domain()


@pytest.mark.parametrize(
    "importer_login,exporter_login",
    (
        (dt.datetime(2021, 10, 1, 12, 1, 1), dt.datetime(2021, 10, 1, 12, 1, 1)),
        (None, None),
    ),
)
def test_user_who_uses_both_platforms_management_context(
    exporter_one_contact, importer_login, exporter_login
):
    exporter_one_contact.exporter_last_login = exporter_login
    exporter_one_contact.importer_last_login = importer_login
    context = UserManagementContext(exporter_one_contact)
    assert context["PLATFORM"] == "Apply for an import licence or export certificate"
    assert context["CASE_OFFICER_EMAIL"] == settings.ILB_CONTACT_EMAIL
    assert (
        context["PLATFORM_LINK"]
        == f"{get_importer_site_domain()} for import or {get_exporter_site_domain()} for export."
    )
