import datetime
from typing import Literal, Optional

from pydantic import BaseModel


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


class GoodsData(BaseModel):
    description: str
    quantity: Optional[float] = None
    controlled_by: Optional[Literal["O", "Q"]] = None


class LicenceData(BaseModel):
    type: Literal["OIL", "DFL", "SIL"]
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
    goods: list[GoodsData]

    # Used when updating a licence
    # Can't be none even though it's optional - lite-hmrc error: "This field may not be null."
    # old_id: Optional[str] = None


class CreateLicenceData(BaseModel):
    licence: LicenceData
