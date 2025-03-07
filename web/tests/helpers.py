from django.conf import settings
from django.contrib.messages import get_messages
from django.core import mail
from django.http import HttpResponse, HttpResponseRedirect
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
    assert personalisation.pop("first_name")
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


def get_messages_from_response(response: HttpResponseRedirect | HttpResponse) -> list[str]:
    return [msg.message for msg in get_messages(response.wsgi_request)]


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
    def cancel_case(application_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        return reverse("case:cancel", kwargs=kwargs)

    @staticmethod
    def close_case(application_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        # Close case is the "post" branch of the manage view
        return reverse("case:manage", kwargs=kwargs)

    @staticmethod
    def edit_import_licence(application_pk: int) -> str:
        """ILB view to edit an import licence."""

        return reverse("import:edit-licence", kwargs={"application_pk": application_pk})

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
    def add_draft_update_request(application_pk: int, case_type: str = "import") -> str:
        kwargs = {
            "application_pk": application_pk,
            "case_type": case_type,
        }
        return reverse("case:add-update-request", kwargs=kwargs)

    @staticmethod
    def edit_update_requests(
        application_pk: int, update_request_pk: int, case_type: str = "import"
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "update_request_pk": update_request_pk,
            "case_type": case_type,
        }
        return reverse("case:edit-update-request", kwargs=kwargs)

    @staticmethod
    def delete_draft_update_request(
        application_pk: int, update_request_pk: int, case_type: str = "import"
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "update_request_pk": update_request_pk,
            "case_type": case_type,
        }
        return reverse("case:delete-update-request", kwargs=kwargs)

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
    def quick_issue(application_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        return reverse("case:quick-issue", kwargs=kwargs)

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
        return reverse("report:report-list-view", kwargs={})

    @staticmethod
    def run_history_view(report_pk: int) -> str:
        kwargs = {"report_pk": report_pk}

        return reverse("report:run-history-view", kwargs=kwargs)

    @staticmethod
    def run_output_view(report_pk: int, schedule_pk: int) -> str:
        kwargs = {"report_pk": report_pk, "schedule_pk": schedule_pk}

        return reverse("report:run-output-view", kwargs=kwargs)

    @staticmethod
    def delete_report_view(report_pk: int, file_pk: int) -> str:
        kwargs = {"report_pk": report_pk, "schedule_pk": file_pk}

        return reverse("report:delete-report-view", kwargs=kwargs)

    @staticmethod
    def download_report_view(report_pk: int, file_pk: int) -> str:
        kwargs = {"report_pk": report_pk, "pk": file_pk}

        return reverse("report:download-report-view", kwargs=kwargs)

    @staticmethod
    def run_report_view(report_pk: int) -> str:
        kwargs = {"report_pk": report_pk}

        return reverse("report:run-report-view", kwargs=kwargs)

    @staticmethod
    def fa_sil_submit(application_pk: int) -> str:
        kwargs = {"application_pk": application_pk}
        return reverse("import:fa-sil:submit", kwargs=kwargs)

    @staticmethod
    def fa_sil_edit(application_pk: int) -> str:
        kwargs = {"application_pk": application_pk}
        return reverse("import:fa-sil:edit", kwargs=kwargs)

    @staticmethod
    def fa_sil_choose_goods_section(application_pk: int) -> str:
        kwargs = {"application_pk": application_pk}
        return reverse("import:fa-sil:choose-goods-section", kwargs=kwargs)

    @staticmethod
    def fa_sil_add_section(application_pk: int, sil_section_type: str) -> str:
        kwargs = {"application_pk": application_pk, "sil_section_type": sil_section_type}
        return reverse("import:fa-sil:add-section", kwargs=kwargs)

    @staticmethod
    def fa_sil_edit_section(application_pk: int, sil_section_type: str, section_pk: int) -> str:
        kwargs = {
            "application_pk": application_pk,
            "sil_section_type": sil_section_type,
            "section_pk": section_pk,
        }
        return reverse("import:fa-sil:edit-section", kwargs=kwargs)

    @staticmethod
    def fa_sil_delete_section(application_pk: int, sil_section_type: str, section_pk: int) -> str:
        kwargs = {
            "application_pk": application_pk,
            "sil_section_type": sil_section_type,
            "section_pk": section_pk,
        }
        return reverse("import:fa-sil:delete-section", kwargs=kwargs)

    @staticmethod
    def fa_sil_set_cover_letter(application_pk: int) -> str:
        kwargs = {"application_pk": application_pk}
        return reverse("import:fa-sil:set-cover-letter", kwargs=kwargs)

    @staticmethod
    def fa_sil_list_goods(application_pk: int) -> str:
        kwargs = {"application_pk": application_pk}
        return reverse("import:fa-sil:list-goods", kwargs=kwargs)

    @staticmethod
    def fa_sil_view_section_5_document(application_pk: int, section5_pk: int) -> str:
        kwargs = {"application_pk": application_pk, "section5_pk": section5_pk}
        return reverse("import:fa-sil:view-section5-document", kwargs=kwargs)

    @staticmethod
    def fa_sil_archive_section_5_document(application_pk: int, section5_pk: int) -> str:
        kwargs = {"application_pk": application_pk, "section5_pk": section5_pk}
        return reverse("import:fa-sil:archive-section5-document", kwargs=kwargs)

    @staticmethod
    def fa_sil_verified_section_5_document(application_pk: int, document_pk: int) -> str:
        kwargs = {"application_pk": application_pk, "document_pk": document_pk}
        return reverse("import:fa-sil:view-verified-section5-document", kwargs=kwargs)

    @staticmethod
    def fa_sil_add_verified_section_5(application_pk: int, section5_pk: int) -> str:
        kwargs = {"application_pk": application_pk, "section5_pk": section5_pk}
        return reverse("import:fa-sil:add-verified-section5", kwargs=kwargs)

    @staticmethod
    def fa_sil_view_verified_section_5(application_pk: int, section5_pk: int) -> str:
        kwargs = {"application_pk": application_pk, "section5_pk": section5_pk}
        return reverse("import:fa-sil:view-verified-section5", kwargs=kwargs)

    @staticmethod
    def fa_sil_delete_verified_section_5(application_pk: int, section5_pk: int) -> str:
        kwargs = {"application_pk": application_pk, "section5_pk": section5_pk}
        return reverse("import:fa-sil:delete-verified-section5", kwargs=kwargs)

    @staticmethod
    def fa_sil_manage_checklist(application_pk: int) -> str:
        kwargs = {"application_pk": application_pk}
        return reverse("import:fa-sil:manage-checklist", kwargs=kwargs)

    @staticmethod
    def fa_sil_response_prep_edit_goods(
        application_pk: int, section_pk: int, sil_section_type: str
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "section_pk": section_pk,
            "sil_section_type": sil_section_type,
        }
        return reverse("import:fa-sil:response-prep-edit-goods", kwargs=kwargs)

    @staticmethod
    def fa_sil_response_prep_reset_goods(
        application_pk: int, section_pk: int, sil_section_type: str
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "section_pk": section_pk,
            "sil_section_type": sil_section_type,
        }
        return reverse("import:fa-sil:response-prep-reset-goods", kwargs=kwargs)

    @staticmethod
    def fa_sil_report_firearm_manual_add(
        application_pk: int, report_pk: int, section_pk: int, sil_section_type: str
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "report_pk": report_pk,
            "section_pk": section_pk,
            "sil_section_type": sil_section_type,
        }

        return reverse("import:fa-sil:report-firearm-manual-add", kwargs=kwargs)

    @staticmethod
    def fa_sil_report_firearm_upload_add(
        application_pk: int, report_pk: int, section_pk: int, sil_section_type: str
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "report_pk": report_pk,
            "section_pk": section_pk,
            "sil_section_type": sil_section_type,
        }

        return reverse("import:fa-sil:report-firearm-upload-add", kwargs=kwargs)

    @staticmethod
    def fa_sil_report_firearm_no_firearm_add(
        application_pk: int, report_pk: int, section_pk: int, sil_section_type: str
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "report_pk": report_pk,
            "section_pk": section_pk,
            "sil_section_type": sil_section_type,
        }

        return reverse("import:fa-sil:report-firearm-no-firearm-add", kwargs=kwargs)

    @staticmethod
    def fa_sil_report_firearm_manual_edit(
        application_pk: int,
        report_pk: int,
        section_pk: int,
        sil_section_type: str,
        report_firearm_pk: int,
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "report_pk": report_pk,
            "section_pk": section_pk,
            "sil_section_type": sil_section_type,
            "report_firearm_pk": report_firearm_pk,
        }

        return reverse("import:fa-sil:report-firearm-manual-edit", kwargs=kwargs)

    @staticmethod
    def fa_sil_report_firearm_upload_view(
        application_pk: int,
        report_pk: int,
        section_pk: int,
        sil_section_type: str,
        report_firearm_pk: int,
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "report_pk": report_pk,
            "section_pk": section_pk,
            "sil_section_type": sil_section_type,
            "report_firearm_pk": report_firearm_pk,
        }

        return reverse("import:fa-sil:report-firearm-upload-view", kwargs=kwargs)

    @staticmethod
    def fa_sil_report_firearm_manual_delete(
        application_pk: int,
        report_pk: int,
        section_pk: int,
        sil_section_type: str,
        report_firearm_pk: int,
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "report_pk": report_pk,
            "section_pk": section_pk,
            "sil_section_type": sil_section_type,
            "report_firearm_pk": report_firearm_pk,
        }

        return reverse("import:fa-sil:report-firearm-manual-delete", kwargs=kwargs)

    @staticmethod
    def fa_oil_submit(application_pk: int) -> str:
        kwargs = {"application_pk": application_pk}
        return reverse("import:fa-oil:submit-oil", kwargs=kwargs)

    @staticmethod
    def fa_oil_manage_checklist(application_pk: int) -> str:
        kwargs = {"application_pk": application_pk}
        return reverse("import:fa-oil:manage-checklist", kwargs=kwargs)

    @staticmethod
    def fa_oil_report_manual_add(application_pk: int, report_pk: int) -> str:
        kwargs = {"application_pk": application_pk, "report_pk": report_pk}

        return reverse("import:fa-oil:report-firearm-manual-add", kwargs=kwargs)

    @staticmethod
    def fa_oil_report_manual_edit(
        application_pk: int, report_pk: int, report_firearm_pk: int
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "report_pk": report_pk,
            "report_firearm_pk": report_firearm_pk,
        }

        return reverse("import:fa-oil:report-firearm-manual-edit", kwargs=kwargs)

    @staticmethod
    def fa_oil_report_manual_delete(
        application_pk: int, report_pk: int, report_firearm_pk: int
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "report_pk": report_pk,
            "report_firearm_pk": report_firearm_pk,
        }

        return reverse("import:fa-oil:report-firearm-manual-delete", kwargs=kwargs)

    @staticmethod
    def fa_oil_report_upload_add(application_pk: int, report_pk: int) -> str:
        kwargs = {"application_pk": application_pk, "report_pk": report_pk}

        return reverse("import:fa-oil:report-firearm-upload-add", kwargs=kwargs)

    @staticmethod
    def fa_oil_report_upload_view(
        application_pk: int, report_pk: int, report_firearm_pk: int
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "report_pk": report_pk,
            "report_firearm_pk": report_firearm_pk,
        }

        return reverse("import:fa-oil:report-firearm-upload-view", kwargs=kwargs)

    @staticmethod
    def fa_dfl_submit(application_pk: int) -> str:
        kwargs = {"application_pk": application_pk}
        return reverse("import:fa-dfl:submit", kwargs=kwargs)

    @staticmethod
    def fa_dfl_edit(application_pk: int) -> str:
        kwargs = {"application_pk": application_pk}
        return reverse("import:fa-dfl:edit", kwargs=kwargs)

    @staticmethod
    def fa_dfl_list_goods(application_pk: int) -> str:
        kwargs = {"application_pk": application_pk}
        return reverse("import:fa-dfl:list-goods", kwargs=kwargs)

    @staticmethod
    def fa_dfl_add_goods(application_pk: int) -> str:
        kwargs = {"application_pk": application_pk}
        return reverse("import:fa-dfl:add-goods", kwargs=kwargs)

    @staticmethod
    def fa_dfl_edit_goods(application_pk: int, document_pk: int) -> str:
        kwargs = {"application_pk": application_pk, "document_pk": document_pk}
        return reverse("import:fa-dfl:edit-goods", kwargs=kwargs)

    @staticmethod
    def fa_dfl_edit_goods_description(application_pk: int, document_pk: int) -> str:
        kwargs = {"application_pk": application_pk, "document_pk": document_pk}
        return reverse("import:fa-dfl:edit-goods-description", kwargs=kwargs)

    @staticmethod
    def fa_dfl_reset_goods_description(application_pk: int, document_pk: int) -> str:
        kwargs = {"application_pk": application_pk, "document_pk": document_pk}
        return reverse("import:fa-dfl:reset-goods-description", kwargs=kwargs)

    @staticmethod
    def fa_dfl_delete_goods(application_pk: int, document_pk: int) -> str:
        kwargs = {"application_pk": application_pk, "document_pk": document_pk}
        return reverse("import:fa-dfl:delete-goods", kwargs=kwargs)

    @staticmethod
    def fa_dfl_view_goods(application_pk: int, document_pk: int) -> str:
        kwargs = {"application_pk": application_pk, "document_pk": document_pk}
        return reverse("import:fa-dfl:view-goods", kwargs=kwargs)

    @staticmethod
    def fa_dfl_manage_checklist(application_pk: int) -> str:
        kwargs = {"application_pk": application_pk}
        return reverse("import:fa-dfl:manage-checklist", kwargs=kwargs)

    @staticmethod
    def fa_dfl_report_manual_add(application_pk: int, report_pk: int, goods_pk: int) -> str:
        kwargs = {"application_pk": application_pk, "report_pk": report_pk, "goods_pk": goods_pk}

        return reverse("import:fa-dfl:report-firearm-manual-add", kwargs=kwargs)

    @staticmethod
    def fa_dfl_report_add_no_firearms(application_pk: int, report_pk: int, goods_pk: int) -> str:
        kwargs = {"application_pk": application_pk, "report_pk": report_pk, "goods_pk": goods_pk}

        return reverse("import:fa-dfl:report-firearm-no-firearm-add", kwargs=kwargs)

    @staticmethod
    def fa_dfl_report_upload_add(application_pk: int, report_pk: int, goods_pk: int) -> str:
        kwargs = {"application_pk": application_pk, "report_pk": report_pk, "goods_pk": goods_pk}

        return reverse("import:fa-dfl:report-firearm-upload-add", kwargs=kwargs)

    @staticmethod
    def fa_dfl_report_view_document(
        application_pk: int,
        report_pk: int,
        report_firearm_pk: int,
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "report_pk": report_pk,
            "report_firearm_pk": report_firearm_pk,
        }

        return reverse("import:fa-dfl:report-firearm-upload-view", kwargs=kwargs)

    @staticmethod
    def fa_dfl_report_manual_edit(
        application_pk: int,
        report_pk: int,
        report_firearm_pk: int,
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "report_pk": report_pk,
            "report_firearm_pk": report_firearm_pk,
        }

        return reverse("import:fa-dfl:report-firearm-manual-edit", kwargs=kwargs)

    @staticmethod
    def fa_dfl_report_manual_delete(
        application_pk: int,
        report_pk: int,
        report_firearm_pk: int,
    ) -> str:
        kwargs = {
            "application_pk": application_pk,
            "report_pk": report_pk,
            "report_firearm_pk": report_firearm_pk,
        }

        return reverse("import:fa-dfl:report-firearm-manual-delete", kwargs=kwargs)

    @staticmethod
    def fa_create_import_contact(application_pk: int, entity: str) -> str:
        kwargs = {"application_pk": application_pk, "entity": entity}
        return reverse("import:fa:create-import-contact", kwargs=kwargs)

    @staticmethod
    def fa_manage_import_contacts(application_pk: int) -> str:
        kwargs = {"application_pk": application_pk}
        return reverse("import:fa:manage-import-contacts", kwargs=kwargs)

    @staticmethod
    def fa_create_report(application_pk: int) -> str:
        kwargs = {"application_pk": application_pk}
        return reverse("import:fa:create-report", kwargs=kwargs)

    @staticmethod
    def fa_provide_report(application_pk: int) -> str:
        kwargs = {"application_pk": application_pk}
        return reverse("import:fa:provide-report", kwargs=kwargs)

    @staticmethod
    def fa_view_report(application_pk: int) -> str:
        kwargs = {"application_pk": application_pk}
        return reverse("import:fa:view-report", kwargs=kwargs)

    @staticmethod
    def download_dfl_case_documents(code: str) -> str:
        return reverse("case:download-dfl-case-documents", kwargs={"code": code})

    @staticmethod
    def regenerate_dfl_case_documents_link(code: str) -> str:
        return reverse("case:regenerate-dfl-case-documents-link", kwargs={"code": code})

    @staticmethod
    def download_case_email_documents(code: str) -> str:
        return reverse("case:download-case-email-documents", kwargs={"code": code})

    @staticmethod
    def regenerate_case_email_documents_link(code: str) -> str:
        return reverse("case:regenerate-case-email-documents-link", kwargs={"code": code})

    @staticmethod
    def opt_view_document(application_pk: int, document_pk: int) -> str:
        kwargs = {"application_pk": application_pk, "document_pk": document_pk}
        return reverse("import:legacy:opt-view-document", kwargs=kwargs)

    @staticmethod
    def opt_checklist(application_pk: int) -> str:
        kwargs = {"application_pk": application_pk}
        return reverse("import:legacy:opt-manage-checklist", kwargs=kwargs)

    @staticmethod
    def textiles_checklist(application_pk: int) -> str:
        kwargs = {"application_pk": application_pk}
        return reverse("import:legacy:tex-manage-checklist", kwargs=kwargs)

    @staticmethod
    def textiles_view_document(application_pk: int, document_pk: int) -> str:
        kwargs = {"application_pk": application_pk, "document_pk": document_pk}
        return reverse("import:legacy:tex-view-document", kwargs=kwargs)

    @staticmethod
    def sps_view_document(application_pk: int, document_pk: int) -> str:
        kwargs = {"application_pk": application_pk, "document_pk": document_pk}
        return reverse("import:legacy:sps-view-supporting-document", kwargs=kwargs)

    @staticmethod
    def sps_view_contract_document(application_pk: int) -> str:
        kwargs = {"application_pk": application_pk}
        return reverse("import:legacy:sps-view-contract-document", kwargs=kwargs)


class SearchURLS:
    @staticmethod
    def search_cases(case_type: str = "import", mode: str = "standard") -> str:
        kwargs = {"case_type": case_type, "mode": mode}

        return reverse("case:search", kwargs=kwargs)

    @staticmethod
    def search_cases_get_results(case_type: str = "import", mode: str = "standard") -> str:
        kwargs = {"case_type": case_type, "mode": mode}

        return reverse("case:search-results", kwargs=kwargs)

    @staticmethod
    def download_spreadsheet(case_type: str = "import") -> str:
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

    @staticmethod
    def copy_export_application_to_cat(application_pk: int) -> str:
        return reverse(
            "case:search-copy-export-app-to-cat",
            kwargs={"application_pk": application_pk, "case_type": "export"},
        )
