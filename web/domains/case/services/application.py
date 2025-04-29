from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpRequest

from web.domains.case.export.utils import copy_template_to_export_application
from web.models import (
    CertificateApplicationTemplate,
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    Country,
    ExportApplicationType,
    Exporter,
    Office,
    Task,
)

from . import document_pack


def create_export_application(
    request: HttpRequest,
    model_class: type[
        CertificateOfFreeSaleApplication
        | CertificateOfManufactureApplication
        | CertificateOfGoodManufacturingPracticeApplication
    ],
    application_type: ExportApplicationType,
    exporter: Exporter,
    exporter_office: Office,
    agent: Exporter | None = None,
    agent_office: Office | None = None,
    app_template: CertificateApplicationTemplate | None = None,
    legacy_create: bool = True,
) -> (
    CertificateOfFreeSaleApplication
    | CertificateOfManufactureApplication
    | CertificateOfGoodManufacturingPracticeApplication
):
    created_by = request.user

    application = model_class()
    application.exporter = exporter
    application.exporter_office = exporter_office
    application.agent = agent
    application.agent_office = agent_office
    application.process_type = model_class.PROCESS_TYPE
    application.created_by = created_by
    application.last_updated_by = created_by
    application.application_type = application_type

    with transaction.atomic():
        application.save()

        if app_template:
            try:
                copy_template_to_export_application(application, app_template, created_by)
            except ValidationError:
                messages.warning(request, "Unable to set all template data.")

            # Refresh in case any template data has been saved.
            application.refresh_from_db()

        Task.objects.create(
            process=application, task_type=Task.TaskType.PREPARE, owner=request.user
        )

        if application.application_type.type_code == ExportApplicationType.Types.GMP:
            # GMP applications are for China only
            country = Country.app.get_gmp_countries().first()
            application.countries.add(country)
        elif (
            application_type.type_code == ExportApplicationType.Types.FREE_SALE
            and not app_template
            # Only create a CFS schedule for legacy create (v2)
            and legacy_create
        ):
            # A template will have already created the schedules in set_template_data
            application.schedules.create(created_by=request.user)

        # Add a draft certificate when creating an application
        # Ensures we never have to check for None
        document_pack.pack_draft_create(application)

    return application
