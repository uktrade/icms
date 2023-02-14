from web.domains.case.utils import add_endorsements_from_application_type
from web.models import (
    DFLApplication,
    EndorsementImportApplication,
    ImportApplicationType,
    Template,
)


def test_add_endorsements_from_application_type(test_import_user, importer, office):
    application_type = ImportApplicationType.objects.get(
        type=ImportApplicationType.Types.FIREARMS, sub_type=ImportApplicationType.SubTypes.DFL
    )

    active_endorsements = Template.objects.filter(
        template_name__startswith="Test Endorsement", is_active=True
    )

    # Add active endorsement to application type
    application_type.endorsements.add(*active_endorsements)

    inactive_endorsement = Template.objects.filter(
        template_type=Template.ENDORSEMENT, is_active=False
    ).first()

    # Add inactive endorsement to application type
    application_type.endorsements.add(inactive_endorsement)

    app = DFLApplication.objects.create(
        created_by=test_import_user,
        last_updated_by=test_import_user,
        importer=importer,
        importer_office=office,
        process_type=DFLApplication.PROCESS_TYPE,
        application_type=application_type,
    )

    add_endorsements_from_application_type(app)

    # Check application only includes active endorsements from application type
    assert app.endorsements.count() == 2
    assert list(app.endorsements.values_list("content", flat=True).order_by("content")) == list(
        active_endorsements.values_list("template_content", flat=True).order_by("template_content")
    )


def test_add_endorsements_from_application_type_added(test_import_user, importer, office):
    application_type = ImportApplicationType.objects.get(
        type=ImportApplicationType.Types.FIREARMS, sub_type=ImportApplicationType.SubTypes.DFL
    )

    endorsements = Template.objects.filter(template_name__startswith="Test Endorsement")

    # Add active endorsements to application type
    application_type.endorsements.add(*endorsements)

    app = DFLApplication.objects.create(
        created_by=test_import_user,
        last_updated_by=test_import_user,
        importer=importer,
        importer_office=office,
        process_type=DFLApplication.PROCESS_TYPE,
        application_type=application_type,
    )

    # Add endorsement to application
    EndorsementImportApplication.objects.create(
        import_application_id=app.pk, content="Test Content"
    )
    add_endorsements_from_application_type(app)

    # Check only endorsement that was one the application is still on the application
    assert app.endorsements.count() == 1
    assert list(app.endorsements.values_list("content", flat=True)) == ["Test Content"]
