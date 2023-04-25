import pytest

from web.models import (
    DerogationsApplication,
    DFLApplication,
    ImportApplicationType,
    IronSteelApplication,
    OpenIndividualLicenceApplication,
    OutwardProcessingTradeApplication,
    PriorSurveillanceApplication,
    Process,
    SanctionsAndAdhocApplication,
    SILApplication,
    TextilesApplication,
    WoodQuotaApplication,
)


@pytest.mark.parametrize(
    "application_model",
    [
        DerogationsApplication,
        DFLApplication,
        IronSteelApplication,
        OpenIndividualLicenceApplication,
        OutwardProcessingTradeApplication,
        PriorSurveillanceApplication,
        SanctionsAndAdhocApplication,
        SILApplication,
        TextilesApplication,
        WoodQuotaApplication,
    ],
)
@pytest.mark.django_db
def test_import_downcast(application_model, importer, test_import_user):
    obj = application_model.objects.create(
        # this is not important for this test, so just hardcode it
        application_type=ImportApplicationType.objects.get(
            type=ImportApplicationType.Types.WOOD_QUOTA
        ),
        created_by=test_import_user,
        last_updated_by=test_import_user,
        importer=importer,
        importer_office=importer.offices.first(),
        process_type=application_model.PROCESS_TYPE,
    )

    # if we already have the specific model, downcast should be a no-op
    assert id(obj) == id(obj.get_specific_model())

    # if we don't, it should load the correct type from the db, and it should be a new instance
    p = Process.objects.get(pk=obj.pk)

    downcast = p.get_specific_model()
    assert type(downcast) is application_model
    assert id(obj) != id(downcast)
