from typing import Optional

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum
from django.forms import model_to_dict
from django.urls import reverse

from web.domains.case._import.derogations.forms import DerogationsChecklistForm
from web.domains.case._import.derogations.models import DerogationsApplication
from web.domains.case._import.fa_dfl.forms import DFLChecklistForm
from web.domains.case._import.fa_dfl.models import DFLApplication
from web.domains.case._import.fa_oil.forms import ChecklistFirearmsOILApplicationForm
from web.domains.case._import.fa_oil.models import OpenIndividualLicenceApplication
from web.domains.case._import.fa_sil.forms import SILChecklistForm
from web.domains.case._import.fa_sil.models import SILApplication
from web.domains.case._import.ironsteel.forms import IronSteelChecklistForm
from web.domains.case._import.ironsteel.models import IronSteelApplication
from web.domains.case._import.models import ImportApplication, ImportApplicationType
from web.domains.case._import.opt.forms import OPTChecklistForm
from web.domains.case._import.opt.models import OutwardProcessingTradeApplication
from web.domains.case._import.sanctions.models import SanctionsAndAdhocApplication
from web.domains.case._import.textiles.forms import TextilesChecklistForm
from web.domains.case._import.textiles.models import TextilesApplication
from web.domains.case._import.wood.forms import WoodQuotaChecklistForm
from web.domains.case._import.wood.models import WoodQuotaApplication
from web.domains.case.export.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    ExportApplication,
)
from web.domains.case.fir.models import FurtherInformationRequest
from web.utils.validation import (
    ApplicationErrors,
    FieldError,
    PageErrors,
    create_page_errors,
)

from . import models
from .types import ApplicationsWithCaseEmail, ApplicationsWithChecklist, ImpOrExp


def get_app_errors(application: ImpOrExp, case_type: str) -> ApplicationErrors:
    application_errors = ApplicationErrors()

    # check for checklist errors
    checklist_errors = get_checklist_errors(application)
    if checklist_errors:
        application_errors.add(checklist_errors)

    # When refusing an application the only thing we check is the checklist.
    if (
        application.is_import_application()
        and application.status == application.Statuses.VARIATION_REQUESTED
        and application.variation_decision == application.REFUSE
    ) or application.decision == application.REFUSE:
        return application_errors

    # Check the response prep screen errors
    response_prep_errors = get_response_preparation_errors(application, case_type)
    if response_prep_errors:
        application_errors.add(response_prep_errors)

    # All other checks.
    if isinstance(application, ImportApplication):
        _get_import_errors(application, application_errors)

    elif isinstance(application, ExportApplication):
        _get_export_errors(application, application_errors)
    else:
        raise ValueError(f"Incorrect application type: {application!r}")

    application_errors.add_many(_get_withdrawals_errors(application, case_type))

    application_errors.add(_get_update_request_errors(application, case_type))

    application_errors.add_many(_get_fir_errors(application, case_type))

    application_errors.add_many(_get_case_notes_errors(application, case_type))

    return application_errors


def _get_import_errors(
    application: ImportApplication, application_errors: ApplicationErrors
) -> None:
    """Add any import application errors"""

    # Application specific checks
    if application.process_type == OpenIndividualLicenceApplication.PROCESS_TYPE:
        application_errors.add_many(_get_fa_oil_errors(application))

    elif application.process_type == DFLApplication.PROCESS_TYPE:
        application_errors.add_many(_get_fa_dfl_errors(application))

    elif application.process_type == SILApplication.PROCESS_TYPE:
        application_errors.add_many(_get_fa_sil_errors(application))

    elif application.process_type == SanctionsAndAdhocApplication.PROCESS_TYPE:
        application_errors.add_many(_get_email_errors(application.sanctionsandadhocapplication, "import"))  # type: ignore[union-attr]

    elif application.process_type == IronSteelApplication.PROCESS_TYPE:
        application_errors.add_many(_get_ironsteel_errors(application.ironsteelapplication))  # type: ignore[union-attr]


def _get_export_errors(
    application: ExportApplication, application_errors: ApplicationErrors
) -> None:
    """Add any export application errors"""

    if application.process_type == CertificateOfFreeSaleApplication.PROCESS_TYPE:
        application_errors.add_many(_get_email_errors(application.certificateoffreesaleapplication, "export"))  # type: ignore[union-attr]

    elif application.process_type == CertificateOfGoodManufacturingPracticeApplication.PROCESS_TYPE:
        application_errors.add_many(
            _get_email_errors(application.certificateofgoodmanufacturingpracticeapplication, "export")  # type: ignore[union-attr]
        )


def _get_fa_oil_errors(application: ImportApplication) -> list[PageErrors]:
    errors = []
    errors.extend(_get_email_errors(application.openindividuallicenceapplication, "import"))  # type: ignore[union-attr]

    return errors


def _get_fa_dfl_errors(application: ImportApplication) -> list[PageErrors]:
    errors = []
    errors.extend(_get_email_errors(application.dflapplication, "import"))  # type: ignore[union-attr]

    return errors


def _get_fa_sil_errors(application: ImportApplication) -> list[PageErrors]:
    errors = []
    errors.extend(_get_email_errors(application.silapplication, "import"))  # type: ignore[union-attr]

    return errors


def _get_ironsteel_errors(application: IronSteelApplication) -> list[PageErrors]:
    errors = []

    certificates = application.certificates.filter(is_active=True)
    total_certificates = certificates.aggregate(sum_requested=Sum("requested_qty")).get(
        "sum_requested"
    )
    if total_certificates != application.quantity:
        for cert in certificates:
            certificate_errors = PageErrors(
                page_name=f"Edit Certificate: {cert.reference}",
                url=reverse(
                    "import:ironsteel:edit-certificate",
                    kwargs={"application_pk": application.pk, "document_pk": cert.pk},
                ),
            )

            certificate_errors.add(
                FieldError(
                    f"Requested Quantity: {cert.requested_qty} kg (imported goods {application.quantity} kg)",
                    messages=[
                        (
                            "Please ensure that the sum of export certificate requested"
                            " quantities equals the total quantity of imported goods."
                        )
                    ],
                )
            )

            errors.append(certificate_errors)

    return errors


def get_checklist_errors(application: ImpOrExp) -> Optional[PageErrors]:
    """Returns any checklist errors for the applications that have a checklist."""

    app_config = {
        OpenIndividualLicenceApplication.PROCESS_TYPE: (
            "import:fa-oil:manage-checklist",
            ChecklistFirearmsOILApplicationForm,
        ),
        DFLApplication.PROCESS_TYPE: ("import:fa-dfl:manage-checklist", DFLChecklistForm),
        SILApplication.PROCESS_TYPE: ("import:fa-sil:manage-checklist", SILChecklistForm),
        WoodQuotaApplication.PROCESS_TYPE: ("import:wood:manage-checklist", WoodQuotaChecklistForm),
        DerogationsApplication.PROCESS_TYPE: (
            "import:derogations:manage-checklist",
            DerogationsChecklistForm,
        ),
        OutwardProcessingTradeApplication.PROCESS_TYPE: (
            "import:opt:manage-checklist",
            OPTChecklistForm,
        ),
        TextilesApplication.PROCESS_TYPE: (
            "import:textiles:manage-checklist",
            TextilesChecklistForm,
        ),
        IronSteelApplication.PROCESS_TYPE: (
            "import:ironsteel:manage-checklist",
            IronSteelChecklistForm,
        ),
    }

    if application.process_type not in app_config.keys():
        return None

    import_app: ApplicationsWithChecklist = application.get_specific_model()

    checklist_url, checklist_form_cls = app_config[application.process_type]

    checklist_errors = PageErrors(
        page_name="Checklist",
        url=reverse(checklist_url, kwargs={"application_pk": import_app.pk}),
    )

    try:
        create_page_errors(
            checklist_form_cls(
                data=model_to_dict(import_app.checklist), instance=import_app.checklist
            ),
            checklist_errors,
        )

    except ObjectDoesNotExist:
        checklist_errors.add(
            FieldError(field_name="Checklist", messages=["Please complete checklist."])
        )

    return checklist_errors


def get_response_preparation_errors(application: ImpOrExp, case_type) -> Optional[PageErrors]:
    """Returns any response preparation errors."""

    prepare_errors = PageErrors(
        page_name="Response Preparation",
        url=reverse(
            "case:prepare-response",
            kwargs={"application_pk": application.pk, "case_type": case_type},
        ),
    )

    is_variation_requested = application.status == application.Statuses.VARIATION_REQUESTED
    is_import = case_type == "import"
    if is_variation_requested and is_import and not application.variation_decision:
        prepare_errors.add(
            FieldError(
                field_name="Variation Decision",
                messages=["Please approve or reject application variation request."],
            )
        )

    if not application.decision:
        prepare_errors.add(
            FieldError(field_name="Decision", messages=["Please approve or reject application."])
        )

    elif case_type == "import" and application.decision == application.APPROVE:
        licence = application.get_most_recent_licence()
        start_date = licence.licence_start_date
        end_date = licence.licence_end_date

        if not start_date:
            prepare_errors.add(
                FieldError(
                    field_name="Licence start date", messages=["Licence start date missing."]
                )
            )

        if not end_date:
            prepare_errors.add(
                FieldError(field_name="Licence end date", messages=["Licence end date missing."])
            )

        if start_date and end_date and end_date <= start_date:
            prepare_errors.add(
                FieldError(
                    field_name="Licence end date",
                    messages=["End date must be after the start date."],
                )
            )

        app_t: ImportApplicationType = application.application_type

        if app_t.paper_licence_flag and app_t.electronic_licence_flag:
            if licence.issue_paper_licence_only is None:
                prepare_errors.add(
                    FieldError(
                        field_name="Issue paper licence only?",
                        messages=["You must enter this item"],
                    )
                )

        if app_t.cover_letter_flag:
            if not application.cover_letter:
                prepare_errors.add(
                    FieldError(field_name="Cover Letter", messages=["You must enter this item"])
                )

    return prepare_errors


def _get_email_errors(application: ApplicationsWithCaseEmail, case_type: str) -> list[PageErrors]:
    errors = []

    drafts = application.case_emails.filter(is_active=True).filter(
        status=models.CaseEmail.Status.DRAFT
    )
    for case_email in drafts:
        email_errors = PageErrors(
            page_name="Drafted Emails",
            url=reverse(
                "case:edit-case-email",
                kwargs={
                    "application_pk": application.pk,
                    "case_email_pk": case_email.pk,
                    "case_type": case_type,
                },
            ),
        )
        email_errors.add(
            FieldError(
                field_name="Status",
                messages=["Email must be closed or deleted before the case can be closed."],
            )
        )

        errors.append(email_errors)

    pending = application.case_emails.filter(is_active=True).filter(
        status=models.CaseEmail.Status.OPEN
    )
    for case_email in pending:
        email_errors = PageErrors(
            page_name="Sent Emails",
            url=reverse(
                "case:add-response-case-email",
                kwargs={
                    "application_pk": application.pk,
                    "case_email_pk": case_email.pk,
                    "case_type": case_type,
                },
            ),
        )
        email_errors.add(
            FieldError(
                field_name="Response",
                messages=["You must enter this item."],
            )
        )

        errors.append(email_errors)

    return errors


def _get_withdrawals_errors(application: ImpOrExp, case_type: str) -> list[PageErrors]:
    errors = []

    open_withdrawls = application.withdrawals.filter(is_active=True).filter(
        status=models.WithdrawApplication.STATUS_OPEN
    )
    for _ in open_withdrawls:
        withdrawal_errors = PageErrors(
            page_name="Withdrawals",
            url=reverse(
                "case:manage-withdrawals",
                kwargs={"application_pk": application.pk, "case_type": case_type},
            ),
        )

        withdrawal_errors.add(
            FieldError(
                field_name="Status",
                messages=[
                    "Application withdrawal requests must be accepted or rejected before the case can be closed."
                ],
            )
        )

        errors.append(withdrawal_errors)

    return errors


def _get_update_request_errors(application: ImpOrExp, case_type: str) -> PageErrors:
    update_request_errors = PageErrors(
        page_name="Application Updates",
        url=reverse(
            "case:list-update-requests",
            kwargs={"application_pk": application.pk, "case_type": case_type},
        ),
    )
    if (
        application.update_requests.filter(is_active=True)
        .exclude(status=models.UpdateRequest.Status.CLOSED)
        .exists()
    ):
        update_request_errors.add(
            FieldError(
                field_name="Status",
                messages=["Application updates must be closed before the case can be closed."],
            )
        )

    return update_request_errors


def _get_fir_errors(application: ImpOrExp, case_type: str) -> list[PageErrors]:
    errors = []

    active_firs = application.further_information_requests.filter(is_active=True).filter(
        status__in=[
            FurtherInformationRequest.DRAFT,
            FurtherInformationRequest.OPEN,
            FurtherInformationRequest.RESPONDED,
        ]
    )

    sent_firs = active_firs.filter(
        status__in=[FurtherInformationRequest.OPEN, FurtherInformationRequest.RESPONDED]
    )
    for fir in sent_firs:
        fir_errors = PageErrors(
            page_name="Sent Further Information Requests",
            url=reverse(
                "case:manage-firs",
                kwargs={
                    "application_pk": application.pk,
                    "case_type": case_type,
                },
            ),
        )

        fir_errors.add(
            FieldError(
                field_name="Status",
                messages=[
                    "Further information requests must be closed or deleted before the case can be closed."
                ],
            )
        )

        errors.append(fir_errors)

    started_firs = active_firs.filter(status=FurtherInformationRequest.DRAFT)
    for fir in started_firs:
        fir_errors = PageErrors(
            page_name="Drafted Further Information Requests",
            url=reverse(
                "case:edit-fir",
                kwargs={"application_pk": application.pk, "case_type": case_type, "fir_pk": fir.pk},
            ),
        )

        fir_errors.add(
            FieldError(
                field_name="Status",
                messages=[
                    "Further information requests must be closed or deleted before the case can be closed."
                ],
            )
        )

        errors.append(fir_errors)

    return errors


def _get_case_notes_errors(application: ImpOrExp, case_type: str) -> list[PageErrors]:
    errors = []

    open_notes = application.case_notes.filter(is_active=True).filter(status=models.CASE_NOTE_DRAFT)
    for note in open_notes:
        note_errors = PageErrors(
            page_name="Case Notes",
            url=reverse(
                "case:edit-note",
                kwargs={
                    "application_pk": application.pk,
                    "case_type": case_type,
                    "note_pk": note.pk,
                },
            ),
        )

        note_errors.add(
            FieldError(
                field_name="Status",
                messages=["Case notes must be completed or deleted before the case can be closed."],
            )
        )

        errors.append(note_errors)

    return errors


def get_org_update_request_errors(application: ImpOrExp, case_type: str) -> PageErrors:
    update_request_errors = PageErrors(
        page_name="Application Updates",
        url=reverse(
            "case:respond-update-request",
            kwargs={"application_pk": application.pk, "case_type": case_type},
        ),
    )

    update_requests = application.update_requests.filter(is_active=True)
    pending_update = update_requests.filter(status=models.UpdateRequest.Status.UPDATE_IN_PROGRESS)
    incomplete_update = update_requests.filter(status=models.UpdateRequest.Status.RESPONDED).filter(
        response_detail__isnull=True
    )

    if pending_update.exists() or incomplete_update.exists():
        update_request_errors.add(
            FieldError(field_name="Summary of Changes", messages=["You must enter this item."])
        )

    return update_request_errors
