import datetime as dt
import json

from web.domains.chief import types
from web.models.shared import EnumJsonEncoder


def test_fa_dfl_licence_data_can_serialise_using_enum_json_encoder():
    """DjangoJSONEncoder doesn't know how to encode enums.

    This class get's used when saving the licence data to the database after the request is sent to chief.
    A new EnumJsonEncoder has been added to encode Enum values.
    """
    today = dt.date.today()
    today_str = today.strftime("%Y-%m-%d")

    fa_dfl_licence = types.FirearmLicenceData(
        type="DFL",
        action="insert",
        id="",
        reference="",
        licence_reference="",
        start_date=today,
        end_date=today,
        organisation=_get_organisation(today),
        country_group="Country Group",
        country_code="Country Code",
        restrictions="Some restrictions",
        goods=[
            types.FirearmGoodsData(
                description="Goods description",
                quantity=12345,
                controlled_by=types.ControlledByEnum.QUANTITY,
                unit=types.QuantityCodeEnum.NUMBER,
            ),
        ],
    )
    create_licence_data = types.LicenceDataPayload(licence=fa_dfl_licence)
    dict_data = create_licence_data.dict()

    licence_json = json.dumps(dict_data, cls=EnumJsonEncoder)
    licence_data = json.loads(licence_json)

    assert licence_data == {
        "licence": {
            "type": "DFL",
            "action": "insert",
            "id": "",
            "reference": "",
            "licence_reference": "",
            "start_date": today_str,
            "end_date": today_str,
            "organisation": {
                "eori_number": "GB123456789012345",
                "name": "Org name",
                "address": {
                    "line_1": "line_1",
                    "line_2": "line_2",
                    "line_3": "line_3",
                    "line_4": "line_4",
                    "line_5": "line_5",
                    "postcode": "postcode",
                },
                "start_date": today_str,
                "end_date": today_str,
            },
            "country_group": "Country Group",
            "country_code": "Country Code",
            "restrictions": "Some restrictions",
            "goods": [
                {
                    "description": "Goods description",
                    "quantity": 12345.0,
                    "controlled_by": "Q",
                    "unit": 30,
                }
            ],
        }
    }


def _get_organisation(today: dt.date) -> types.OrganisationData:
    return types.OrganisationData(
        eori_number="GB123456789012345",
        name="Org name",
        address=types.AddressData(
            line_1="line_1",
            line_2="line_2",
            line_3="line_3",
            line_4="line_4",
            line_5="line_5",
            postcode="postcode",
        ),
        start_date=today,
        end_date=today,
    )
