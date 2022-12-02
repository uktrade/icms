import datetime
from enum import Enum, IntEnum
from typing import Literal

from pydantic import BaseModel, validator


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


class OrganisationData(BaseModel):
    eori_number: str
    name: str
    address: AddressData
    start_date: datetime.date | None = None
    end_date: datetime.date | None = None

    @validator("eori_number")
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


class LicenceDataBase(BaseModel):
    type: Literal["OIL", "DFL", "SIL", "SAN"]
    action: Literal["insert", "cancel", "replace"]

    id: str  # UUID for this licence payload
    reference: str  # Case reference
    licence_reference: str

    start_date: datetime.date
    end_date: datetime.date

    organisation: OrganisationData

    country_group: str | None = None
    country_code: str | None = None
    restrictions: str


class FirearmGoodsData(BaseModel):
    description: str
    quantity: float | None = None
    controlled_by: ControlledByEnum | None = None
    unit: QuantityCodeEnum | None = None


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
    licence: FirearmLicenceData | SanctionsLicenceData


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
