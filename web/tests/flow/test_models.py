import pytest

from web.flow.models import ProcessTypes
from web.models import Process


@pytest.mark.django_db
def test_downcast_unknown():
    p = Process(process_type="blaa")

    with pytest.raises(NotImplementedError, match="Unknown process_type blaa"):
        p.get_specific_model()


@pytest.mark.parametrize(
    "process_type,expected_label",
    [
        (ProcessTypes.FA_DFL, "Firearms and Ammunition"),
        (ProcessTypes.FA_OIL, "Firearms and Ammunition"),
        (ProcessTypes.FA_SIL, "Firearms and Ammunition"),
        (ProcessTypes.TEXTILES, "Textiles"),
        (ProcessTypes.WOOD, "Wood"),
        (ProcessTypes.DEROGATIONS, "Sanctions Derogation"),
        (ProcessTypes.SPS, "Prior Surveillance"),
        (ProcessTypes.SANCTIONS, "Sanctions and Adhoc"),
        (ProcessTypes.OPT, "Outward Processing Trade"),
        (ProcessTypes.CFS, "CFS Application"),
        (ProcessTypes.COM, "COM Application"),
        (ProcessTypes.GMP, "GMP Application"),
        ("Unknown PT", "Application Details"),
    ],
)
def test_get_application_details_link(process_type, expected_label):
    process = Process(process_type=process_type)

    assert process.get_application_details_link() == expected_label
