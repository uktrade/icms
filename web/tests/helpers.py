from django.conf import settings
from django.core import mail
from django.test.client import Client
from django.urls import reverse
from django.utils import timezone

from web.domains.case.types import ImpOrExp
from web.flow.models import ProcessTypes
from web.mail.constants import EmailTypes
from web.models import (
    ApprovalRequest,
    Exporter,
    ExporterAccessRequest,
    ExporterApprovalRequest,
    Importer,
    ImporterAccessRequest,
    ImporterApprovalRequest,
    User,
    VariationRequest,
)
from web.utils.validation import ApplicationErrors


def get_test_client(server_name: str, user: User | None = None) -> Client:
    """Create a test client, optionally logging in a user.

    :param server_name: Domain to link to the correct site.
    :param user: User to log in if value is supplied.

    """
    client = Client(SERVER_NAME=server_name)

    if user:
        assert client.login(username=user.username, password="test") is True, "Failed to login"

    return client


def check_page_errors(
    errors: ApplicationErrors,
    page_name: str,
    error_field_names: list[str],
) -> None:
    """Check if the supplied errors have the expected errors for the given page."""

    page_errors = errors.get_page_errors(page_name)

    assert page_errors is not None

    actual_error_names = sorted(e.field_name for e in page_errors.errors)

    assert sorted(error_field_names) == actual_error_names, f"Actual errors: {actual_error_names}"


def check_pages_checked(error: ApplicationErrors, expected_pages_checked: list[str]) -> None:
    """Check if the supplied pages have been checked."""

    checked = sorted(e.page_name for e in error.page_errors)

    assert sorted(expected_pages_checked) == checked, f"Actual checked pages: {checked}"


def check_email_was_sent(
    exp_num_emails: int,
    exp_sent_to: str,
    exp_subject: str,
    exp_in_body: str | None = None,
    exp_attachments: list[tuple[str, bytes]] | None = None,
) -> None:
    outbox = mail.outbox
    assert len(outbox) == exp_num_emails
    if exp_num_emails:
        sent_email = outbox[exp_num_emails - 1]
        assert sent_email.to == [exp_sent_to]
        assert sent_email.subject == exp_subject

        if exp_in_body:
            assert exp_in_body in sent_email.body

        if exp_attachments:
            assert exp_attachments == sent_email.attachments


def check_gov_notify_email_was_sent(
    exp_num_emails: int,
    exp_sent_to: list,
    exp_email_name: EmailTypes,
    exp_personalisation: dict,
    exp_subject: str | None = "",
    exp_in_body: str | None = "",
) -> None:
    outbox = mail.outbox
    assert len(outbox) == exp_num_emails
    sent_to = [_email.to[0] for _email in outbox]
    assert sorted(sent_to) == sorted(exp_sent_to)

    if exp_num_emails:
        sent_email = outbox[exp_num_emails - 1]
        assert sent_email.name == exp_email_name
        act_personalisation = sent_email.get_personalisation()
        assert_common_email_personalisation(act_personalisation, exp_subject, exp_in_body)
        assert act_personalisation == exp_personalisation


def assert_common_email_personalisation(personalisation: dict, exp_subject: str, exp_in_body: str):
    assert personalisation.pop("icms_contact_email") == settings.ILB_CONTACT_EMAIL
    assert personalisation.pop("icms_contact_phone") == settings.ILB_CONTACT_PHONE
    assert "icms_url" in personalisation
    assert personalisation.pop("subject") == exp_subject
    assert exp_in_body in personalisation.pop("body")


def add_variation_request_to_app(
    application: ImpOrExp,
    user: User,
    what_varied: str = "Dummy what_varied",
    status: VariationRequest.Statuses = VariationRequest.Statuses.OPEN,
    extension_flag: bool = False,
) -> VariationRequest:
    return application.variation_requests.create(
        status=status,
        what_varied=what_varied,
        why_varied="Dummy why_varied",
        when_varied=timezone.now().date(),
        requested_by=user,
        extension_flag=extension_flag,
    )


def get_linked_access_request(
    access_request: ImporterAccessRequest | ExporterAccessRequest,
    org: Importer | Exporter,
) -> ImporterAccessRequest | ExporterAccessRequest:
    access_request.link = org
    access_request.save()
    return access_request


def add_approval_request(
    access_request: ImporterAccessRequest | ExporterAccessRequest,
    requested_by: User,
    requested_from: User | None = None,
    status: str = ApprovalRequest.Statuses.OPEN,
):
    match access_request:
        case ImporterAccessRequest():
            process_type = ProcessTypes.ImpApprovalReq
            model_cls = ImporterApprovalRequest

        case ExporterAccessRequest():
            process_type = ProcessTypes.ExpApprovalReq
            model_cls = ExporterApprovalRequest
        case _:
            raise ValueError(f"invalid access request: {access_request}")

    return model_cls.objects.create(
        access_request=access_request,
        process_type=process_type,
        status=status,
        requested_by=requested_by,
        requested_from=requested_from,
    )


class CaseURLS:
    """Collection of Case Urls for convenience when testing."""

    # web/domains/case/views/views_misc.py urls
    @staticmethod
    def take_ownership(application_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        return reverse("case:take-ownership", kwargs=kwargs)

    @staticmethod
    def reassign_ownership(application_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        return reverse("case:reassign-ownership", kwargs=kwargs)

    @staticmethod
    def manage(application_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        return reverse("case:manage", kwargs=kwargs)

    @staticmethod
    def close_case(application_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        # Close case is the "post" branch of the manage view
        return reverse("case:manage", kwargs=kwargs)

    @staticmethod
    def add_fir(application_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        return reverse("case:add-fir", kwargs=kwargs)

    @staticmethod
    def respond_to_fir(application_pk: int, fir_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "fir_pk": fir_pk, "case_type": case_type}

        return reverse("case:respond-fir", kwargs=kwargs)

    @staticmethod
    def delete_fir(application_pk: int, fir_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "fir_pk": fir_pk, "case_type": case_type}

        return reverse("case:delete-fir", kwargs=kwargs)

    @staticmethod
    def withdraw_fir(application_pk: int, fir_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "fir_pk": fir_pk, "case_type": case_type}

        return reverse("case:withdraw-fir", kwargs=kwargs)

    @staticmethod
    def close_fir(application_pk: int, fir_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "fir_pk": fir_pk, "case_type": case_type}

        return reverse("case:close-fir", kwargs=kwargs)

    @staticmethod
    def edit_fir(application_pk: int, fir_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "fir_pk": fir_pk, "case_type": case_type}

        return reverse("case:edit-fir", kwargs=kwargs)

    @staticmethod
    def manage_withdrawals(application_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        return reverse("case:manage-withdrawals", kwargs=kwargs)

    @staticmethod
    def archive_withdrawal(
        application_pk: int, withdrawal_pk: int, case_type: str = "import"
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "withdrawal_pk": withdrawal_pk,
            "case_type": case_type,
        }
        return reverse("case:archive-withdrawal", kwargs=kwargs)

    @staticmethod
    def withdrawal_case(application_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}
        return reverse("case:withdraw-case", kwargs=kwargs)

    # web/domains/case/views/views_update_request.py urls
    @staticmethod
    def list_update_requests(application_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        return reverse("case:list-update-requests", kwargs=kwargs)

    @staticmethod
    def manage_update_requests(application_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}
        return reverse("case:manage-update-requests", kwargs=kwargs)

    @staticmethod
    def start_update_request(
        application_pk: int, update_request_pk: int, case_type: str = "import"
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "case_type": case_type,
            "update_request_pk": update_request_pk,
        }
        return reverse("case:start-update-request", kwargs=kwargs)

    @staticmethod
    def close_update_request(
        application_pk: int, update_request_pk: int, case_type: str = "import"
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "case_type": case_type,
            "update_request_pk": update_request_pk,
        }
        return reverse("case:close-update-request", kwargs=kwargs)

    @staticmethod
    def respond_update_request(application_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}
        return reverse("case:respond-update-request", kwargs=kwargs)

    # web/domains/case/views/views_fir.py urls
    @staticmethod
    def manage_firs(application_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        return reverse("case:manage-firs", kwargs=kwargs)

    # web/domains/case/views/views_note.py urls
    @staticmethod
    def list_notes(application_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        return reverse("case:list-notes", kwargs=kwargs)

    # web/domains/case/views/views_prepare_response.py urls
    @staticmethod
    def prepare_response(application_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        return reverse("case:prepare-response", kwargs=kwargs)

    @staticmethod
    def manage_case_emails(application_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}
        return reverse("case:manage-case-emails", kwargs=kwargs)

    @staticmethod
    def create_case_emails(application_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}
        return reverse("case:create-case-email", kwargs=kwargs)

    @staticmethod
    def edit_case_emails(application_pk: int, case_email_pk: int, case_type: str = "import") -> str:
        kwargs = {
            "application_pk": application_pk,
            "case_type": case_type,
            "case_email_pk": case_email_pk,
        }
        return reverse("case:edit-case-email", kwargs=kwargs)

    @staticmethod
    def archive_case_emails(
        application_pk: int, case_email_pk: int, case_type: str = "import"
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "case_type": case_type,
            "case_email_pk": case_email_pk,
        }
        return reverse("case:archive-case-email", kwargs=kwargs)

    @staticmethod
    def add_response_case_emails(
        application_pk: int, case_email_pk: int, case_type: str = "import"
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "case_type": case_type,
            "case_email_pk": case_email_pk,
        }
        return reverse("case:add-response-case-email", kwargs=kwargs)

    @staticmethod
    def manage_variations(application_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        return reverse("case:variation-request-manage", kwargs=kwargs)

    @staticmethod
    def cancel_variation_request(
        application_pk: int, variation_request_pk: int, case_type: str = "import"
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "case_type": case_type,
            "variation_request_pk": variation_request_pk,
        }

        return reverse("case:variation-request-cancel", kwargs=kwargs)

    @staticmethod
    def variation_request_request_update(
        application_pk: int, variation_request_pk: int, case_type: str = "import"
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "case_type": case_type,
            "variation_request_pk": variation_request_pk,
        }

        return reverse("case:variation-request-request-update", kwargs=kwargs)

    @staticmethod
    def variation_request_cancel_update_request(
        application_pk: int, variation_request_pk: int
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "case_type": "import",
            "variation_request_pk": variation_request_pk,
        }

        return reverse("case:variation-request-cancel-request-update", kwargs=kwargs)

    @staticmethod
    def variation_request_submit_update(
        application_pk: int, variation_request_pk: int, case_type: str = "import"
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "case_type": case_type,
            "variation_request_pk": variation_request_pk,
        }

        return reverse("case:variation-request-submit-update", kwargs=kwargs)

    @staticmethod
    def start_authorisation(application_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        return reverse("case:start-authorisation", kwargs=kwargs)

    @staticmethod
    def authorise_documents(application_pk: int, case_type="import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        return reverse("case:authorise-documents", kwargs=kwargs)

    @staticmethod
    def licence_preview(application_pk: int, case_type="import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        return reverse("case:licence-preview", kwargs=kwargs)

    @staticmethod
    def licence_pre_sign(application_pk: int, case_type="import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        return reverse("case:licence-pre-sign", kwargs=kwargs)

    @staticmethod
    def preview_cover_letter(application_pk: int, case_type="import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        return reverse("case:cover-letter-preview", kwargs=kwargs)

    @staticmethod
    def check_document_generation(application_pk: int, case_type="import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        return reverse("case:check-document-generation", kwargs=kwargs)

    @staticmethod
    def view_issued_case_documents(
        application_pk: int, issued_document_pk: int, case_type="import"
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "case_type": case_type,
            "issued_document_pk": issued_document_pk,
        }

        return reverse("case:view-issued-case-documents", kwargs=kwargs)

    @staticmethod
    def clear_issued_case_documents_from_workbasket(
        application_pk: int, issued_document_pk: int, case_type="import"
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "case_type": case_type,
            "issued_document_pk": issued_document_pk,
        }

        return reverse("case:clear-issued-case-documents", kwargs=kwargs)

    @staticmethod
    def clear_case_from_workbasket(application_pk: int, case_type="import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        return reverse("case:clear", kwargs=kwargs)

    @staticmethod
    def get_application_history(application_pk: int, case_type="import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        return reverse("case:ilb-case-history", kwargs=kwargs)

    @staticmethod
    def check_chief_progress(application_pk: int) -> str:
        kwargs = {"application_pk": application_pk}

        return reverse("chief:check-progress", kwargs=kwargs)

    @staticmethod
    def constabulary_documents(application_pk: int, doc_pack_pk: int, case_type="import") -> str:
        kwargs = {
            "application_pk": application_pk,
            "doc_pack_pk": doc_pack_pk,
            "case_type": case_type,
        }
        return reverse("case:constabulary-doc", kwargs=kwargs)

    @staticmethod
    def constabulary_documents_download(
        application_pk: int, doc_pack_pk: int, cdr_pk: int, case_type="import"
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "doc_pack_pk": doc_pack_pk,
            "case_type": case_type,
            "cdr_pk": cdr_pk,
        }
        return reverse("case:constabulary-doc-download", kwargs=kwargs)

    @staticmethod
    def report_list_view() -> str:
        return reverse("report-list-view", kwargs={})

    @staticmethod
    def run_history_view(report_pk: int) -> str:
        kwargs = {"report_pk": report_pk}

        return reverse("run-history-view", kwargs=kwargs)

    @staticmethod
    def run_output_view(report_pk: int, schedule_pk: int) -> str:
        kwargs = {"report_pk": report_pk, "schedule_pk": schedule_pk}

        return reverse("run-output-view", kwargs=kwargs)

    @staticmethod
    def download_report_view(report_pk: int, file_pk: int) -> str:
        kwargs = {"report_pk": report_pk, "pk": file_pk}

        return reverse("download-report-view", kwargs=kwargs)

    @staticmethod
    def run_report_view(report_pk: int) -> str:
        kwargs = {"report_pk": report_pk}

        return reverse("run-report-view", kwargs=kwargs)

    @staticmethod
    def fa_sil_report_manual_add(
        application_pk: int, report_pk: int, section_pk: int, sil_section_type: str
    ):
        kwargs = {
            "application_pk": application_pk,
            "report_pk": report_pk,
            "section_pk": section_pk,
            "sil_section_type": sil_section_type,
        }

        return reverse("import:fa-sil:report-firearm-manual-add", kwargs=kwargs)

    @staticmethod
    def fa_sil_report_no_firearm_add(
        application_pk: int, report_pk: int, section_pk: int, sil_section_type: str
    ):
        kwargs = {
            "application_pk": application_pk,
            "report_pk": report_pk,
            "section_pk": section_pk,
            "sil_section_type": sil_section_type,
        }

        return reverse("import:fa-sil:report-firearm-no-firearm-add", kwargs=kwargs)

    @staticmethod
    def fa_oil_report_manual_add(application_pk: int, report_pk: int):
        kwargs = {"application_pk": application_pk, "report_pk": report_pk}

        return reverse("import:fa-oil:report-firearm-manual-add", kwargs=kwargs)

    @staticmethod
    def fa_oil_report_upload_add(application_pk: int, report_pk: int):
        kwargs = {"application_pk": application_pk, "report_pk": report_pk}

        return reverse("import:fa-oil:report-firearm-upload-add", kwargs=kwargs)

    @staticmethod
    def fa_dfl_report_manual_add(application_pk: int, report_pk: int, goods_pk: int):
        kwargs = {"application_pk": application_pk, "report_pk": report_pk, "goods_pk": goods_pk}

        return reverse("import:fa-dfl:report-firearm-manual-add", kwargs=kwargs)

    @staticmethod
    def fa_create_import_contact(application_pk: int, entity: str):
        kwargs = {"application_pk": application_pk, "entity": entity}
        return reverse("import:fa:create-import-contact", kwargs=kwargs)

    @staticmethod
    def fa_create_report(application_pk: int):
        kwargs = {"application_pk": application_pk}
        return reverse("import:fa:create-report", kwargs=kwargs)


class SearchURLS:
    @staticmethod
    def search_cases(case_type: str = "import", mode: str = "standard"):
        kwargs = {"case_type": case_type, "mode": mode}

        return reverse("case:search", kwargs=kwargs)

    @staticmethod
    def search_cases_get_results(case_type: str = "import", mode: str = "standard"):
        kwargs = {"case_type": case_type, "mode": mode}

        return reverse("case:search-results", kwargs=kwargs)

    @staticmethod
    def download_spreadsheet(case_type: str = "import"):
        kwargs = {"case_type": case_type}

        return reverse("case:search-download-spreadsheet", kwargs=kwargs)

    @staticmethod
    def reopen_case(application_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        return reverse("case:search-reopen-case", kwargs=kwargs)

    @staticmethod
    def request_variation(application_pk: int, case_type: str = "import") -> str:
        return reverse(
            "case:search-request-variation",
            kwargs={"application_pk": application_pk, "case_type": case_type},
        )

    @staticmethod
    def open_variation(application_pk: int) -> str:
        case_type = "export"

        return reverse(
            "case:search-open-variation",
            kwargs={"application_pk": application_pk, "case_type": case_type},
        )

    @staticmethod
    def revoke_licence(application_pk: int, case_type: str = "import") -> str:
        return reverse(
            "case:search-revoke-case",
            kwargs={"application_pk": application_pk, "case_type": case_type},
        )

    @staticmethod
    def reassign_case_owner(case_type: str = "import") -> str:
        return reverse("case:search-reassign-case-owner", kwargs={"case_type": case_type})

    @staticmethod
    def copy_export_application(application_pk: int) -> str:
        return reverse(
            "case:search-copy-export-application",
            kwargs={"application_pk": application_pk, "case_type": "export"},
        )
