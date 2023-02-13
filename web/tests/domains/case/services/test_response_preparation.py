import pytest

from web.domains.case.services import response_preparation
from web.models import (
    DFLApplication,
    EndorsementImportApplication,
    ImportApplicationType,
    Template,
)


@pytest.mark.django_db
def test_add_endorsements_from_applciation_type(test_import_user, importer, office):
    application_type = ImportApplicationType.objects.get(
        type=ImportApplicationType.Types.FIREARMS, sub_type=ImportApplicationType.SubTypes.DFL
    )

    endorsements = Template.objects.filter(template_name__startswith="Test Endorsement")
    application_type.endorsements.add(*endorsements)

    inactive_endorsement = Template.objects.filter(
        template_type=Template.ENDORSEMENT, is_active=False
    ).first()

    application_type.endorsements.add(inactive_endorsement)

    app = DFLApplication.objects.create(
        created_by=test_import_user,
        last_updated_by=test_import_user,
        importer=importer,
        importer_office=office,
        process_type=DFLApplication.PROCESS_TYPE,
        application_type=application_type,
    )

    response_preparation.add_endorsements_from_application_type(app)

    assert app.endorsements.count() == 2
    assert list(app.endorsements.values_list("content", flat=True).order_by("content")) == list(
        endorsements.values_list("template_content", flat=True).order_by("template_content")
    )


@pytest.mark.django_db
def test_add_endorsements_from_applciation_type_added(test_import_user, importer, office):
    application_type = ImportApplicationType.objects.get(
        type=ImportApplicationType.Types.FIREARMS, sub_type=ImportApplicationType.SubTypes.DFL
    )

    endorsements = Template.objects.filter(template_name__startswith="Test Endorsement")
    application_type.endorsements.add(*endorsements)

    app = DFLApplication.objects.create(
        created_by=test_import_user,
        last_updated_by=test_import_user,
        importer=importer,
        importer_office=office,
        process_type=DFLApplication.PROCESS_TYPE,
        application_type=application_type,
    )

    EndorsementImportApplication.objects.create(
        import_application_id=app.pk, content="Test Content"
    )
    response_preparation.add_endorsements_from_application_type(app)

    assert app.endorsements.count() == 1
    assert list(app.endorsements.values_list("content", flat=True)) == ["Test Content"]
