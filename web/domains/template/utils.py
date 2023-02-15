from web.domains.case._import.models import (
    EndorsementImportApplication,
    ImportApplication,
)


def add_endorsements_from_application_type(application: ImportApplication) -> None:
    """Adds active endorsements to application based on application type"""

    application_type = application.application_type

    if application.endorsements.exists():
        # If there are already endorsements on the application, do not add default endorsements
        return

    endorsements = application_type.endorsements.filter(is_active=True)

    EndorsementImportApplication.objects.bulk_create(
        [
            EndorsementImportApplication(
                import_application_id=application.pk,
                content=endorsement.template_content,
            )
            for endorsement in endorsements
        ]
    )


def add_template_data_on_submit(application: ImportApplication) -> None:
    """Adds data required for applications response preparation on submit"""

    application_type = application.application_type

    if application_type.endorsements_flag:
        add_endorsements_from_application_type(application)

    # TODO ICMSLST-1914 Expand to include cover letters
