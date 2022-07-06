import datetime
from enum import Enum, IntEnum
from typing import Literal, Optional, Union

from pydantic import BaseModel


# https://www.gov.uk/government/publications/uk-trade-tariff-quantity-codes/uk-trade-tariff-quantity-codes
class QuantityCodeEnum(IntEnum):
    """HMRC Quantity Code values seen in ICMS - extend as needed."""

    KG = 23
    NUMBER = 30
    PAIR = 31
    SQUARE_METRE = 45
    CUBIC_METRE = 87


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
    postcode: str


# TODO: ICMSLST-1658 All examples in DEV supply TRADER_ID instead of TURN for the
#       Work out what field it should be
# <TURN/>
# <TRADER_ID>GBN1234567890123</TRADER_ID>
class OrganisationData(BaseModel):
    eori_number: str
    # turn: Optional[str] # (eori_number or turn)

    name: str
    address: AddressData
    start_date: Optional[datetime.date] = None
    end_date: Optional[datetime.date] = None


class LicenceDataBase(BaseModel):
    type: Literal["OIL", "DFL", "SIL", "SAN"]
    action: Literal["insert", "cancel", "update"]

    id: str  # This is the uuid
    reference: str  # Licence reference
    case_reference: str  # Transaction reference

    start_date: datetime.date
    end_date: datetime.date

    organisation: OrganisationData

    country_group: Optional[str] = None
    country_code: Optional[str] = None
    restrictions: str

    # Used when updating a licence
    # Can't be none even though it's optional - lite-hmrc error: "This field may not be null."
    # old_id: Optional[str] = None


class FirearmGoodsData(BaseModel):
    description: str
    quantity: Optional[float] = None
    controlled_by: Optional[ControlledByEnum] = None
    unit: Optional[QuantityCodeEnum] = None


class FirearmLicenceData(LicenceDataBase):
    type: Literal["OIL", "DFL", "SIL"]
    goods: list[FirearmGoodsData]


class SanctionGoodsData(BaseModel):
    commodity: str
    quantity: float
    # This is hardcoded to Q rather than having to specify it for each record.
    controlled_by: Literal[ControlledByEnum.QUANTITY] = ControlledByEnum.QUANTITY
    unit: QuantityCodeEnum


class SanctionsLicenceData(LicenceDataBase):
    type: Literal["SAN"]
    goods: list[SanctionGoodsData]


class CreateLicenceData(BaseModel):
    licence: Union[FirearmLicenceData, SanctionsLicenceData]
