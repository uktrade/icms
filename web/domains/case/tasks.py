import io

from celery import chord
from django.db import transaction
from django.utils import timezone

from config.celery import app
from web.domains.case.models import CaseDocumentReference, VariationRequest
from web.domains.case.shared import ImpExpStatus
from web.domains.case.types import ImpOrExp
from web.domains.case.utils import (
    end_process_task,
    set_application_licence_or_certificate_active,
)
from web.domains.chief import client
from web.domains.file.models import File
from web.domains.user.models import User
from web.flow.models import Process, Task
from web.utils.pdf import DocumentTypes, PdfGenerator
from web.utils.s3 import delete_file_from_s3, upload_file_obj_to_s3
from web.utils.sentry import capture_exception, capture_message


def create_case_document_pack(application: ImpOrExp, user: User) -> None:
    # Success / Error task
    # called after all tasks have finished
    callback = create_document_pack_on_success.si(application.id, user.id).on_error(
        create_document_pack_on_error.s(application_pk=application.id, user_pk=user.id)
    )

    # Create the tasks that will generate the documents
    if application.is_import_application():
        licence = application.get_latest_issued_document()
        header = [
            create_import_application_document.si(application.id, licence.pk, cdr.pk, user.id)
            for cdr in licence.document_references.all()
        ]
    else:
        certificate = application.get_latest_issued_document()
        header = [
            create_export_application_document.si(application.id, certificate.pk, cdr.pk, user.id)
            for cdr in certificate.document_references.all()
        ]

    # Queue the documents to be generated.
    chord(header=header, body=callback).apply_async()


@app.task(name="web.domains.case.tasks.create_import_application_document")
def create_import_application_document(
    application_pk: int, licence_pk: int, casedocumentreference_pk: int, user_pk: int
) -> None:
    with transaction.atomic():
        user = User.objects.get(pk=user_pk)

        application = Process.objects.get(pk=application_pk).get_specific_model()
        licence = application.licences.get(pk=licence_pk)
        document_reference = licence.document_references.select_for_update().get(
            pk=casedocumentreference_pk
        )

        if document_reference.document_type == CaseDocumentReference.Type.LICENCE:
            doc_type = DocumentTypes.LICENCE_SIGNED
            filename = "import-licence.pdf"

        elif document_reference.document_type == CaseDocumentReference.Type.COVER_LETTER:
            doc_type = DocumentTypes.COVER_LETTER
            filename = "cover-letter.pdf"

        else:
            raise ValueError(
                f"Unable to generate document - unsupported document type {document_reference.document_type}"
            )

        # Delete old document if it exists.
        # This happens if the application is sent to CHIEF but there is an error, and it is now being resent.
        if document_reference.document:
            delete_file_from_s3(path=document_reference.document.path)

        file_obj = io.BytesIO()
        pdf_gen = PdfGenerator(application=application, licence=licence, doc_type=doc_type)
        pdf_gen.get_pdf(target=file_obj)

        # Reset read point to start of stream before uploading
        file_obj.seek(0)
        upload_case_document_file(file_obj, document_reference, filename, user)


@app.task(name="web.domains.case.tasks.create_export_application_document")
def create_export_application_document(
    application_pk: int, certificate_pk: int, casedocumentreference_pk: int, user_pk: int
) -> None:
    # TODO: Revisit when we can generate an export certificate:
    # https://uktrade.atlassian.net/browse/ICMSLST-1406
    # https://uktrade.atlassian.net/browse/ICMSLST-1407
    # https://uktrade.atlassian.net/browse/ICMSLST-1408
    print("*************************** SKIPPING FOR NOW")


@app.task(name="web.domains.case.tasks.create_document_pack_on_success")
def create_document_pack_on_success(application_pk, user_pk):
    with transaction.atomic():
        # Transition application on to correct status
        application = (
            Process.objects.select_for_update().get(pk=application_pk).get_specific_model()
        )
        user = User.objects.get(pk=user_pk)

        task = application.get_expected_task(Task.TaskType.DOCUMENT_SIGNING)
        end_process_task(task, user)

        is_import = application.is_import_application()

        if is_import and application.application_type.chief_flag:
            client.send_application_to_chief(application, task)
        else:
            if application.status == ImpExpStatus.VARIATION_REQUESTED:
                vr = application.variation_requests.get(status=VariationRequest.OPEN)
                vr.status = VariationRequest.ACCEPTED if is_import else VariationRequest.CLOSED

                # On export applications we record the date closed and who closed it.
                if not is_import:
                    vr.closed_by = user
                    vr.closed_datetime = timezone.now()

                vr.save()

            application.status = ImpExpStatus.COMPLETED
            application.save()

            set_application_licence_or_certificate_active(application)


@app.task(name="web.domains.case.tasks.create_document_pack_on_error")
def create_document_pack_on_error(
    request, exc, traceback, *args, application_pk, user_pk, **kwargs
):
    capture_message(f"create_case_document_pack Task {request.id!r} raised error: {exc!r}")
    capture_exception()

    with transaction.atomic():
        # Transition application on to correct status
        application = Process.objects.get(pk=application_pk)
        user = User.objects.get(pk=user_pk)

        task = application.get_expected_task(Task.TaskType.DOCUMENT_SIGNING)
        end_process_task(task, user)
        Task.objects.create(
            process=application, task_type=Task.TaskType.DOCUMENT_ERROR, previous=task
        )


def upload_case_document_file(
    file_obj: io.BytesIO, cdr: "CaseDocumentReference", filename: str, created_by: "User"
) -> None:
    """Upload a case document file to s3 and create related data."""

    # application id - document type - case document reference id - timestamp - filename
    time_stamp = f'{timezone.now().strftime("%Y%m%d%H%M%S")}'
    key = f"{cdr.object_id}_{cdr.document_type}_{cdr.id}_{time_stamp}_{filename}"

    file_size = upload_file_obj_to_s3(file_obj, key)

    cdr.document = File.objects.create(
        is_active=True,
        filename=filename,
        content_type="application/pdf",
        file_size=file_size,
        path=key,
        created_by=created_by,
    )
    cdr.save()


# NOTE: Leaving this here for now as it's useful to easily test celery tasks.
# def chord_testing(application_id):
#     callback = on_chord_success.si(application_id).on_error(
#         on_chord_error.s(application_pk=application_id)
#     )
#     header = [
#         test_create.si(application_id, f"doc_type_{x}") for x in range(4)
#     ]
#     chord(header=header, body=callback).apply_async()
#
#
# @app.task(name="web.domains.case.tasks.test_create")
# def test_create(application_pk, document_type):
#     print(
#         f"CREATE THE FOLLOWING DOCUMENT -> application_pk: {application_pk}, document_type: {document_type}"
#     )
#
#     if document_type == "doc_type_2":
#         raise ValueError("This isn't correct")
#
#
# @app.task(name="web.domains.case.tasks.on_chord_success")
# def on_chord_success(*, application_pk):
#     print("*" * 80)
#     print("SUCCESS OUTCOME")
#
#
# @app.task(name="web.domains.case.tasks.on_chord_error")
# def on_chord_error(request, exc, traceback, *args, application_pk, **kwargs):
#     print("FAILURE OUTCOME")
#     print(request)
#     print(args)
#     print(kwargs)
#     print(application_pk)
#     print("Task {0!r} raised error: {1!r}".format(request.id, exc))
#     print("*" * 160)
