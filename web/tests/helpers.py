from django.urls import reverse

from web.utils.validation import ApplicationErrors


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


def check_pages_checked(error: ApplicationErrors, expected_pages_checked: list[str]) -> bool:
    """Check if the supplied pages have been checked."""

    checked = sorted(e.page_name for e in error.page_errors)

    assert sorted(expected_pages_checked) == checked, f"Actual checked pages: {checked}"


class CaseURLS:
    """Collection of Case Urls for convenience when testing."""

    # web/domains/case/views/views_misc.py urls
    @staticmethod
    def take_ownership(application_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        return reverse("case:take-ownership", kwargs=kwargs)

    @staticmethod
    def manage(application_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        return reverse("case:manage", kwargs=kwargs)

    @staticmethod
    def close_case(application_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        # Close case is the the "post" branch of the manage view
        return reverse("case:manage", kwargs=kwargs)

    @staticmethod
    def manage_withdrawals(application_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        return reverse("case:manage-withdrawals", kwargs=kwargs)

    # web/domains/case/views/views_update_request.py urls
    @staticmethod
    def manage_update_requests(application_pk: int, case_type: str = "import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        return reverse("case:manage-update-requests", kwargs=kwargs)

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
    ):
        kwargs = {
            "application_pk": application_pk,
            "case_type": case_type,
            "variation_request_pk": variation_request_pk,
        }

        return reverse("case:variation-request-request-update", kwargs=kwargs)

    @staticmethod
    def variation_request_cancel_update_request(application_pk: int, variation_request_pk: int):
        kwargs = {
            "application_pk": application_pk,
            "case_type": "import",
            "variation_request_pk": variation_request_pk,
        }

        return reverse("case:variation-request-cancel-request-update", kwargs=kwargs)

    @staticmethod
    def variation_request_submit_update(
        application_pk: int, variation_request_pk: int, case_type: str = "import"
    ):
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

        return reverse("case:preview-cover-letter", kwargs=kwargs)

    @staticmethod
    def check_document_generation(application_pk: int, case_type="import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        return reverse("case:check-document-generation", kwargs=kwargs)

    @staticmethod
    def get_application_history(application_pk: int, case_type="import") -> str:
        kwargs = {"application_pk": application_pk, "case_type": case_type}

        return reverse("case:history", kwargs=kwargs)


class SearchURLS:
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
    def open_variation(application_pk):
        case_type = "export"

        return reverse(
            "case:search-open-variation",
            kwargs={"application_pk": application_pk, "case_type": case_type},
        )
