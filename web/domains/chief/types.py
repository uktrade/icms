import datetime as dt
from enum import Enum, IntEnum
from typing import Literal

from pydantic import BaseModel, field_validator


# https://www.gov.uk/government/publications/uk-trade-tariff-quantity-codes/uk-trade-tariff-quantity-codes
class QuantityCodeEnum(IntEnum):
    """HMRC Quantity Code values seen in ICMS - extend as needed."""

    #  1. Weight
    WEIGHT_OUNCE = 11
    WEIGHT_POUND = 12
    WEIGHT_CENTAL_100LB = 13
    WEIGHT_CWT = 14
    WEIGHT_1000LB = 15
    WEIGHT_TON = 16
    WEIGHT_OZ_Troy = 17
    WEIGHT_LB_Troy = 18
    WEIGHT_GRAMME = 21
    WEIGHT_HECTOGRAMME_100_gms = 22
    WEIGHT_KILOGRAMME = 23
    WEIGHT_100_kgs = 24
    WEIGHT_TONNE = 25
    WEIGHT_METRIC_Carat = 26
    WEIGHT_50_kgs = 27

    # 2. Gross weight
    GROSS_WEIGHT_POUND_GROSS = 60
    GROSS_WEIGHT_KILOGRAMME_GROSS = 61
    GROSS_WEIGHT_QUINTAL_100_KGS_GROSS = 62

    # 3. Unit
    UNIT_NUMBER = 30
    UNIT_PAIR = 31
    UNIT_DOZEN = 32
    UNIT_DOZEN_PAIR = 33
    UNIT_HUNDRED = 34
    UNIT_LONG_HUNDRED = 35
    UNIT_GROSS = 36
    UNIT_THOUSAND = 37
    UNIT_SHORT_STANDARD = 38

    # 4. Area
    AREA_SQUARE_INCH = 41
    AREA_SQUARE_FOOT = 42
    AREA_SQUARE_YARD = 43
    AREA_SQUARE_DECIMETRE = 44
    AREA_SQUARE_METRE = 45
    AREA_100_SQUARE_METRES = 46

    # 5. Length
    LENGTH_INCH = 50
    LENGTH_FOOT = 51
    LENGTH_YARD = 52
    LENGTH_100_FEET = 53
    LENGTH_MILLIMETRE = 54
    LENGTH_CENTIMETRE = 55
    LENGTH_DECIMETRE = 56
    LENGTH_METRE = 57
    LENGTH_DEKAMETRE = 58
    LENGTH_HECTOMETRE = 59

    # 6. Capacity
    CAPACITY_PINT = 71
    CAPACITY_GALLON = 72
    CAPACITY_36_gallons_Bulk_barrel = 73
    CAPACITY_MILLILITRE_CU_CENTIMETRE = 74
    CAPACITY_CENTILITRE = 75
    CAPACITY_LITRE = 76
    CAPACITY_DEKALITRE = 77
    CAPACITY_HECTOLITRE = 78
    CAPACITY_US_Gallon = 79
    CAPACITY_1000_LITRE = 40

    # 7. Volume
    VOLUME_CUBIC_INCH = 81
    VOLUME_CUBIC_FOOT = 82
    VOLUME_CUBIC_YARD = 83
    VOLUME_STANDARD = 84
    VOLUME_PILED_CUBIC_FATHOM = 85
    VOLUME_CUBIC_DECIMETRE = 86
    VOLUME_CUBIC_METRE = 87
    VOLUME_PILED_CUBIC_METRE = 88
    VOLUME_GRAM_FISSILE_ISOTOPES = 89

    # TODO: Enable these if they are ever required.
    #       Currently disabled as they are the only code with 0 prefix and would therefore have to
    #       change this serialiaser to a StrEnum and would require more testing.
    # 8. Various
    # VARIOUS_KILOGRAMME_OF_H2O2 = 29
    # VARIOUS_KILOGRAMME_OF_K2O = 01
    # VARIOUS_KILOGRAMME_OF_KOH = 02
    # VARIOUS_KILOGRAMME_OF_N = 03
    # VARIOUS_KILOGRAMME_OF_NAOH = 04
    # VARIOUS_KILOGRAMME_OF_P2O5 = 05
    # VARIOUS_KILOGRAMME_OF_U = 06
    # VARIOUS_KILOGRAMME_OF_WO3 = 07
    # VARIOUS_NUMBER_OF_FLASKS = 08
    # VARIOUS_NUMBER_OF_KITS = 09
    # VARIOUS_NUMBER_OF_ROLLS = 10
    # VARIOUS_NUMBER_OF_SETS = 19
    # VARIOUS_100_PACKS = 20
    # VARIOUS_1000_TABLETS = 28
    # VARIOUS_100_KILOGRAM_NET_DRY_MATTER = 48
    # VARIOUS_100_KILOGRAM_DRAINED_NET_WEIGHT = 49
    # VARIOUS_KILOGRAM_OF_CHOLINE_CHLORIDE = 107
    # VARIOUS_KILOGRAM_OF_METHYL_AMINES = 39
    # VARIOUS_KILOGRAMME_OF_TOTAL_ALCOHOL = 63
    # VARIOUS_CCT_CARRYING_CAPACITY_IN_TONNES_METRIC_SHIPPING = 64
    # VARIOUS_GRAM_FINE_GOLD_CONTENT = 65
    # VARIOUS_LITRE_OF_ALCOHOL = 66
    # VARIOUS_LITRE_OF_ALCOHOL_IN_THE_SPIRIT = 66
    # VARIOUS_LITRE_OF_PURE_100_ALCOHOL = 66
    # VARIOUS_KILOGRAMME_90_DRY = 67
    # VARIOUS_90_TONNE_DRY = 68
    # VARIOUS_KILOGRAMME_DRAINED_NET_WEIGHT = 69
    # VARIOUS_STANDARD_LITRE_OF_HYDROCARBON_OIL = 70
    # VARIOUS_1000_CUBIC_METRES = 80
    # VARIOUS_CURIE = 90
    # VARIOUS_PROOF_GALLON = 91
    # VARIOUS_DISPLACEMENT_TONNAGE = 92
    # VARIOUS_GROSS_TONNAGE = 93
    # VARIOUS_100_INTERNATIONAL_UNITS = 94
    # VARIOUS_MILLION_INTERNATIONAL_UNITS_POTENCY = 95
    # VARIOUS_KILOWATT = 96
    # VARIOUS_KILOWATT_HOUR = 97
    # VARIOUS_ALCOHOL_BY_VOLUME_ABV_BEER = 98
    # VARIOUS_DEGREES_PERCENTAGE_VOLUME = 99
    # VARIOUS_TJ_GROSS_CALORIFIC_VALUE = 120
    # VARIOUS_EURO_PER_TONNE_OF_FUEL = 112
    # VARIOUS_EURO_PER_TONNE_NET_OF_BIODIESEL_CONTENT = 113
    # VARIOUS_KILOMETRES = 114
    # VARIOUS_EURO_PER_TONNE_NET_OF_BIOETHANOL_CONTENT = 115
    # VARIOUS_NUMBER_OF_WATT = 117
    # VARIOUS_KILOGRAM_RAW_SUGAR = 118
    # VARIOUS_KAC_KG_NET_OF_ACESULFAME_POTASSIUM = 119


class ControlledByEnum(Enum):
    """HMRC Controlled by values.

    Only OPEN and QUANTITY are currently used.
    """

    # VALUE_AND_QUANTITY = "B"  # Both Value and Quantity
    OPEN = "O"  # Open (no usage recording or control)
    QUANTITY = "Q"  # Quantity Only
    # VALUE = "V"  # Value Only


class AddressData(BaseModel):
    line_1: str
    line_2: str = ""
    line_3: str = ""
    line_4: str = ""
    line_5: str = ""
    postcode: str = ""


class OrganisationData(BaseModel):
    eori_number: str
    name: str
    address: AddressData
    start_date: dt.date | None = None
    end_date: dt.date | None = None

    @field_validator("eori_number")
    @classmethod
    def eori_number_must_be_valid(cls, v):
        """Basic validation for EORI number.

        https://www.tax.service.gov.uk/check-eori-number
        """

        # This may need to be extended to include other prefixes (XI) in the future.
        if not v.upper().startswith("GB"):
            raise ValueError("Must start with 'GB' prefix")

        # Example value: GB123456789012345
        eori_number_length = len(v[2:])

        if eori_number_length != 12 and eori_number_length != 15:
            raise ValueError("Must start with 'GB' followed by 12 or 15 numbers")

        return v


class LicenceDataPayloadBase(BaseModel):
    """Base class for all licence data payload records."""

    type: Literal["OIL", "DFL", "SIL", "SAN"]
    action: Literal["insert", "cancel", "replace"]

    id: str  # UUID for this licence payload
    reference: str  # Case reference (Unique in licenceData file - Used as transactionRef field)
    licence_reference: str  # Used as chief licenceRef field

    start_date: dt.date
    end_date: dt.date


class CancelLicencePayload(LicenceDataPayloadBase):
    """Class used to send a cancel record to HMRC"""

    action: Literal["cancel"]


class InsertAndReplaceBase(LicenceDataPayloadBase):
    """Class used to send an insert or replace record to HMRC"""

    action: Literal["insert", "replace"]

    organisation: OrganisationData

    country_group: str | None = None
    country_code: str | None = None
    restrictions: str


class FirearmGoodsData(BaseModel):
    description: str
    quantity: float | None = None
    controlled_by: ControlledByEnum | None = None
    unit: QuantityCodeEnum | None = None


class FirearmLicenceData(InsertAndReplaceBase):
    type: Literal["OIL", "DFL", "SIL"]
    goods: list[FirearmGoodsData]


class SanctionGoodsData(BaseModel):
    commodity: str
    quantity: float
    # This is hardcoded to Q rather than having to specify it for each record.
    controlled_by: Literal[ControlledByEnum.QUANTITY] = ControlledByEnum.QUANTITY
    unit: QuantityCodeEnum


class SanctionsLicenceData(InsertAndReplaceBase):
    type: Literal["SAN"]
    goods: list[SanctionGoodsData]


class LicenceDataPayload(BaseModel):
    """Payload that gets sent to ICMS-HRMC."""

    licence: FirearmLicenceData | SanctionsLicenceData | CancelLicencePayload


#
# CHIEF Response types
#
class AcceptedLicence(BaseModel):
    id: str


class ResponseError(BaseModel):
    error_code: int
    error_msg: str


class RejectedLicence(BaseModel):
    id: str
    errors: list[ResponseError]


class ChiefLicenceReplyResponseData(BaseModel):
    run_number: int
    accepted: list[AcceptedLicence]
    rejected: list[RejectedLicence]


class UsageRecord(BaseModel):
    licence_ref: str
    licence_status: Literal["C", "E", "O", "S", "D"]


class ChiefUsageDataResponseData(BaseModel):
    usage_data: list[UsageRecord]
