import datetime as dt

import pytest

from web.domains.chief.serializers import (
    fa_dfl_serializer,
    fa_oil_serializer,
    fa_sil_serializer,
    fix_licence_reference,
    get_organisation,
    get_restrictions,
    sanction_serializer,
)
from web.domains.chief.types import (
    AddressData,
    ControlledByEnum,
    FirearmGoodsData,
    FirearmLicenceData,
    LicenceDataPayload,
    OrganisationData,
    QuantityCodeEnum,
    SanctionGoodsData,
    SanctionsLicenceData,
)
from web.flow.models import ProcessTypes


@pytest.mark.parametrize(
    ["process_type", "licence_reference", "expected_licence_ref"],
    [
        (ProcessTypes.FA_DFL, "GBSIL0000002C", "GBSIL0000002C"),
        (ProcessTypes.FA_OIL, "GBOIL0000003D", "GBOIL0000003D"),
        (ProcessTypes.FA_SIL, "GBSIL0000004E", "GBSIL0000004E"),
        (ProcessTypes.SPS, "GBAOG0000006G", "GBAOG0000006G"),
        (ProcessTypes.SANCTIONS, "GBSAN0000007H", "GBSAN0000007H"),
        (ProcessTypes.TEXTILES, "GBTEX0000008X", "GBTEX0000008X"),
        (ProcessTypes.FA_DFL, "0000010K", "GBSIL0000010K"),
        (ProcessTypes.FA_OIL, "0000011L", "GBOIL0000011L"),
        (ProcessTypes.FA_SIL, "0000012M", "GBSIL0000012M"),
        (ProcessTypes.SPS, "0000014B", "GBAOG0000014B"),
        (ProcessTypes.SANCTIONS, "0000015C", "GBSAN0000015C"),
        (ProcessTypes.TEXTILES, "0000016D", "GBTEX0000016D"),
    ],
)
def test_fix_licence_reference(process_type, licence_reference, expected_licence_ref):
    chief_lr = fix_licence_reference(process_type, licence_reference)

    assert chief_lr == expected_licence_ref


class TestGetRestrictions:
    @pytest.fixture(autouse=True)
    def setup(self, _fa_sil):
        self.app = _fa_sil
        self.app.endorsements.create(content="This is some content")
        self.app.endorsements.create(content="This is some more content")

    def test_get_restrictions_content_below_limit(self):
        expected = "This is some content\nThis is some more content"
        actual = get_restrictions(self.app)

        assert expected == actual

    def test_get_restrictions_truncates_content_when_limit_exceeded(self):
        expected = "This is some content\nThis<trc>"
        actual = get_restrictions(self.app, limit=30)

        assert expected == actual

    def test_get_restrictions_when_content_equal_to_limit(self):
        expected = "This is some content\nThis is some more content"
        actual = get_restrictions(self.app, limit=46)

        assert expected == actual


class TestImporterData:
    @pytest.fixture(autouse=True)
    def setup(self, _fa_sil):
        self.app = _fa_sil

    def test_organisation_importer_fields(self):
        expected = OrganisationData(
            eori_number="GB0123456789ABCDE",
            name="Test Importer 1",
            address=AddressData(
                line_1="I1 address line 1",
                line_2="I1 address line 2",
                line_3="",
                line_4="",
                line_5="",
                postcode="BT180LZ",  # /PS-IGNORE
            ),
            start_date=None,
            end_date=None,
        )
        assert expected == get_organisation(self.app)

    def test_individual_importer_fields(self, importer_individual):
        self.app.importer = importer_individual
        self.app.importer_office = importer_individual.offices.first()
        expected = OrganisationData(
            eori_number="GBPR",
            name="individual_importer_user_first_name individual_importer_user_last_name",
            address=AddressData(
                line_1="1 Individual Road",
                line_2="Individual City",
                line_3="",
                line_4="",
                line_5="",
                postcode="XX123XX",  # /PS-IGNORE
            ),
            start_date=None,
            end_date=None,
        )
        assert expected == get_organisation(self.app)


def test_fa_sil_serializer(fa_sil_app_processing):
    app = fa_sil_app_processing
    expected = LicenceDataPayload(
        licence=FirearmLicenceData(
            type="SIL",
            action="insert",
            id="1234",
            reference="IMA/2024/00001",
            licence_reference="GBSIL0000001B",
            start_date=dt.date(2020, 6, 1),
            end_date=dt.date(2024, 12, 31),
            organisation=OrganisationData(
                eori_number="GB0123456789ABCDE",
                name="Test Importer 1",
                address=AddressData(
                    line_1="I1 address line 1",
                    line_2="I1 address line 2",
                    line_3="",
                    line_4="",
                    line_5="",
                    postcode="BT180LZ",  # /PS-IGNORE
                ),
                start_date=None,
                end_date=None,
            ),
            country_group=None,
            country_code="AF",
            restrictions=(
                "Not valid for items originating in or consigned from Iran, North Korea, Libya, Syria, Belarus or the Russian Federation "
                "(including any previous name by which these territories have been known)."
            ),
            goods=[
                FirearmGoodsData(
                    description="Section 1 goods to which Section 1 of the Firearms Act 1968, as amended, applies.",
                    quantity=111.0,
                    controlled_by=ControlledByEnum.QUANTITY,
                    unit=QuantityCodeEnum.NUMBER,
                ),
                FirearmGoodsData(
                    description="Section 2 goods to which Section 2 of the Firearms Act 1968, as amended, applies.",
                    quantity=222.0,
                    controlled_by=ControlledByEnum.QUANTITY,
                    unit=QuantityCodeEnum.NUMBER,
                ),
                FirearmGoodsData(
                    description="Section 5 goods to which Section 5(A) of the Firearms Act 1968, as amended, applies.",
                    quantity=333.0,
                    controlled_by=ControlledByEnum.QUANTITY,
                    unit=QuantityCodeEnum.NUMBER,
                ),
                FirearmGoodsData(
                    description="Unlimited Section 5 goods to which Section 5(A) of the Firearms Act 1968, as amended, applies.",
                    quantity=None,
                    controlled_by=ControlledByEnum.OPEN,
                    unit=None,
                ),
                FirearmGoodsData(
                    description=(
                        "Section 58 obsoletes goods chambered in the obsolete calibre .22 Extra Long Maynard to which Section 58(2) of the "
                        "Firearms Act 1968, as amended, applies."
                    ),
                    quantity=444.0,
                    controlled_by=ControlledByEnum.QUANTITY,
                    unit=QuantityCodeEnum.NUMBER,
                ),
                FirearmGoodsData(
                    description="Section 58 other goods to which Section 58(2) of the Firearms Act 1968, as amended, applies.",
                    quantity=555.0,
                    controlled_by=ControlledByEnum.QUANTITY,
                    unit=QuantityCodeEnum.NUMBER,
                ),
            ],
        )
    )
    assert expected == fa_sil_serializer(app, "insert", "1234")


def test_fa_dfl_serializer(fa_dfl_app_pre_sign):
    app = fa_dfl_app_pre_sign
    expected = LicenceDataPayload(
        licence=FirearmLicenceData(
            type="DFL",
            action="insert",
            id="1234",
            reference="IMA/2024/00001",
            licence_reference="GBSIL0000001B",
            start_date=dt.date(2020, 6, 1),
            end_date=dt.date(2024, 12, 31),
            organisation=OrganisationData(
                eori_number="GB0123456789ABCDE",
                name="Test Importer 1",
                address=AddressData(
                    line_1="I1 address line 1",
                    line_2="I1 address line 2",
                    line_3="",
                    line_4="",
                    line_5="",
                    postcode="BT180LZ",  # /PS-IGNORE
                ),
                start_date=None,
                end_date=None,
            ),
            country_group=None,
            country_code="AF",
            restrictions=(
                "Not valid for items originating in or consigned from Iran, North Korea, Libya, Syria, Belarus or the Russian Federation "
                "(including any previous name by which these territories have been known)."
            ),
            goods=[
                FirearmGoodsData(
                    description="goods_description value",
                    quantity=None,
                    controlled_by=None,
                    unit=None,
                )
            ],
        )
    )
    assert expected == fa_dfl_serializer(app, "insert", "1234")


def test_fa_oil_serializer(fa_oil_app_processing):
    app = fa_oil_app_processing
    expected = LicenceDataPayload(
        licence=FirearmLicenceData(
            type="OIL",
            action="insert",
            id="1234",
            reference="IMA/2024/00001",
            licence_reference="GBOIL0000001B",
            start_date=dt.date(2020, 6, 1),
            end_date=dt.date(2024, 12, 31),
            organisation=OrganisationData(
                eori_number="GB0123456789ABCDE",
                name="Test Importer 1",
                address=AddressData(
                    line_1="I1 address line 1",
                    line_2="I1 address line 2",
                    line_3="",
                    line_4="",
                    line_5="",
                    postcode="BT180LZ",  # /PS-IGNORE
                ),
                start_date=None,
                end_date=None,
            ),
            country_group="G001",
            country_code=None,
            restrictions=(
                "OPEN INDIVIDUAL LICENCE Not valid for goods originating in or consigned from Iran, "
                "North Korea, Libya, Syria, Belarus or the Russian Federation (including any previous "
                "name by which these territories have been known). \n\nThis licence is only valid if "
                "the firearm and its essential component parts (Barrel, frame, receiver (including both "
                "upper or lower receiver), slide, cylinder, bolt or breech block) are marked with name of "
                "manufacturer or brand, country or place of manufacturer, serial number and the  year of "
                "manufacture (if not part of the serial number) and model (where feasible). If an essential "
                "component is too small to be fully marked it must at least be marked with a serial number "
                "or alpha-numeric or digital code. If the item is not marked as set out above you have 1 "
                "month from entry into the UK to comply with this requirement. If the item is being imported "
                "for deactivation, you have three months to either comply or have the item deactivated.\nItems "
                "must be marked using the Latin alphabet and the Arabic numeral system. The font size must be "
                "at least 1,6 mm unless the relevant component parts are too small to be marked to this size, "
                "in which case a smaller font size may be used. \nFor frames or receivers made from a "
                "non-metallic material, the marking should be applied to a metal plate that is permanently "
                "embedded in the material of the frame or receiver in such a way that the plate cannot be easily "
                "or readily removed; and removing the plate would destroy a portion of the frame or receiver.  "
                "Other techniques for marking such frames or receivers are permitted, provided those techniques "
                "ensure an equivalent level of clarity and permanence for the marking."
            ),
            goods=[
                FirearmGoodsData(
                    description=(
                        "Firearms, component parts thereof, or ammunition of any applicable commodity code, "
                        "other than those falling under Section 5 of the Firearms Act 1968 as amended."
                    ),
                    quantity=None,
                    controlled_by=None,
                    unit=None,
                )
            ],
        )
    )
    assert expected == fa_oil_serializer(app, "insert", "1234")


def test_sanction_serializer(sanctions_app_processing):
    app = sanctions_app_processing
    expected = LicenceDataPayload(
        licence=SanctionsLicenceData(
            type="SAN",
            action="insert",
            id="1234",
            reference="IMA/2024/00001",
            licence_reference="GBSAN0000001B",
            start_date=dt.date(2020, 6, 1),
            end_date=dt.date(2024, 12, 31),
            organisation=OrganisationData(
                eori_number="GB0123456789ABCDE",
                name="Test Importer 1",
                address=AddressData(
                    line_1="I1 address line 1",
                    line_2="I1 address line 2",
                    line_3="",
                    line_4="",
                    line_5="",
                    postcode="BT180LZ",  # /PS-IGNORE
                ),
                start_date=None,
                end_date=None,
            ),
            country_group=None,
            country_code="BY",
            restrictions="",
            goods=[
                SanctionGoodsData(
                    commodity="4202199090",
                    quantity=1000.0,
                    controlled_by=ControlledByEnum.QUANTITY,
                    unit=QuantityCodeEnum.NUMBER,
                ),
                SanctionGoodsData(
                    commodity="9013109000",
                    quantity=56.78,
                    controlled_by=ControlledByEnum.QUANTITY,
                    unit=QuantityCodeEnum.NUMBER,
                ),
            ],
        )
    )
    assert expected == sanction_serializer(app, "insert", "1234")
