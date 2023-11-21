import pytest

from web.domains.chief.serializers import fix_licence_reference
from web.flow.models import ProcessTypes


@pytest.mark.parametrize(
    ["process_type", "licence_reference", "expected_licence_ref"],
    [
        (ProcessTypes.DEROGATIONS, "GBSAN0000001B", "GBSAN0000001B"),
        (ProcessTypes.FA_DFL, "GBSIL0000002C", "GBSIL0000002C"),
        (ProcessTypes.FA_OIL, "GBOIL0000003D", "GBOIL0000003D"),
        (ProcessTypes.FA_SIL, "GBSIL0000004E", "GBSIL0000004E"),
        (ProcessTypes.IRON_STEEL, "GBAOG0000005F", "GBAOG0000005F"),
        (ProcessTypes.SPS, "GBAOG0000006G", "GBAOG0000006G"),
        (ProcessTypes.SANCTIONS, "GBSAN0000007H", "GBSAN0000007H"),
        (ProcessTypes.TEXTILES, "GBTEX0000008X", "GBTEX0000008X"),
        (ProcessTypes.DEROGATIONS, "0000009J", "GBSAN0000009J"),
        (ProcessTypes.FA_DFL, "0000010K", "GBSIL0000010K"),
        (ProcessTypes.FA_OIL, "0000011L", "GBOIL0000011L"),
        (ProcessTypes.FA_SIL, "0000012M", "GBSIL0000012M"),
        (ProcessTypes.IRON_STEEL, "0000013A", "GBAOG0000013A"),
        (ProcessTypes.SPS, "0000014B", "GBAOG0000014B"),
        (ProcessTypes.SANCTIONS, "0000015C", "GBSAN0000015C"),
        (ProcessTypes.TEXTILES, "0000016D", "GBTEX0000016D"),
    ],
)
def test_fix_licence_reference(process_type, licence_reference, expected_licence_ref):
    chief_lr = fix_licence_reference(process_type, licence_reference)

    assert chief_lr == expected_licence_ref
