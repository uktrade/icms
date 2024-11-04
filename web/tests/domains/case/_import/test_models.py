import pytest
from django.db.utils import IntegrityError
from django.urls import reverse

from web.models import (
    DFLApplication,
    ImportApplicationType,
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
        DFLApplication,
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
def test_import_downcast(application_model, importer, importer_one_contact):
    obj = application_model.objects.create(
        # this is not important for this test, so just hardcode it
        application_type=ImportApplicationType.objects.get(
            type=ImportApplicationType.Types.WOOD_QUOTA
        ),
        created_by=importer_one_contact,
        last_updated_by=importer_one_contact,
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


def test_display_status_for_completed_sil_app(completed_sil_app):
    assert completed_sil_app.is_import_application() is True
    assert completed_sil_app.get_status_display() == "Completed"


def test_display_status_for_rejected_app(complete_rejected_app):
    assert complete_rejected_app.is_import_application() is True
    assert complete_rejected_app.get_status_display() == "Completed (Refused)"


def test_display_status_for_in_progress_app(fa_dfl_app_in_progress):
    assert fa_dfl_app_in_progress.is_import_application() is True
    assert fa_dfl_app_in_progress.get_status_display() == "In Progress"


@pytest.mark.django_db
def test_create_application_url_error():
    application = ImportApplicationType.objects.first()
    application.type = "HELLO"
    with pytest.raises(ValueError, match="Unknown Application Type: HELLO"):
        application.create_application_url


@pytest.mark.django_db
def test_create_fa_application_url_error():
    application = ImportApplicationType.objects.filter(type="FA").first()
    application.sub_type = "HELLO"
    with pytest.raises(ValueError, match="Unknown Firearms Application Sub Type: HELLO"):
        application.create_application_url


@pytest.mark.parametrize(
    "sub_type,exp_url",
    (
        (ImportApplicationType.SubTypes.DFL, reverse("import:create-fa-dfl")),
        (ImportApplicationType.SubTypes.OIL, reverse("import:create-fa-oil")),
        (ImportApplicationType.SubTypes.SIL, reverse("import:create-fa-sil")),
    ),
)
@pytest.mark.django_db
def test_create_fa_application_url(sub_type, exp_url):
    application = ImportApplicationType.objects.get(type="FA", sub_type=sub_type)
    assert application.create_application_url == exp_url


@pytest.mark.parametrize(
    "_type,exp_url",
    (
        (ImportApplicationType.Types.SANCTION_ADHOC, reverse("import:create-sanctions")),
        (ImportApplicationType.Types.WOOD_QUOTA, reverse("import:create-wood-quota")),
        (ImportApplicationType.Types.SPS, reverse("import:create-sps")),
    ),
)
@pytest.mark.django_db
def test_create_application_url(_type, exp_url):
    application = ImportApplicationType.objects.get(type=_type)
    assert application.create_application_url == exp_url


@pytest.mark.django_db
def test_type_contstraint():
    with pytest.raises(
        IntegrityError,
        match='duplicate key value violates unique constraint "unique_import_app_type"',
    ):
        ImportApplicationType.objects.create(
            type=ImportApplicationType.Types.OPT,
            sub_type="QUOTA",
            name="DUPLICATE APPLICATION",
            is_active=True,
            sigl_flag=False,
            chief_flag=False,
            paper_licence_flag=False,
            electronic_licence_flag=False,
            cover_letter_flag=False,
            cover_letter_schedule_flag=False,
            category_flag=False,
            quantity_unlimited_flag=False,
            exp_cert_upload_flag=False,
            supporting_docs_upload_flag=False,
            multiple_commodities_flag=False,
            usage_auto_category_desc_flag=False,
            case_checklist_flag=False,
            importer_printable=False,
            declaration_template_id=1,
        )
