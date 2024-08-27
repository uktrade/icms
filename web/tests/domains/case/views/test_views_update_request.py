from django.core import mail
from django.test.client import Client
from pytest_django.asserts import assertContains, assertTemplateUsed

from web.domains.case.types import ImpOrExp
from web.mail.constants import EmailTypes
from web.mail.url_helpers import (
    get_case_view_url,
    get_update_request_view_url,
    get_validate_digital_signatures_url,
)
from web.models import ImportApplication, UpdateRequest, User
from web.sites import SiteName, get_importer_site_domain
from web.tests.application_utils import resubmit_app
from web.tests.helpers import CaseURLS, check_gov_notify_email_was_sent


def get_open_update_request(
    client: Client, app: ImpOrExp, post: dict | None = None
) -> UpdateRequest:
    if post is None:
        post = {"request_subject": "subject", "request_detail": "detail", "send": "true"}

    assert app.update_requests.count() == 0
    assert app.status == ImportApplication.Statuses.SUBMITTED

    client.post(CaseURLS.take_ownership(app.pk))

    response = client.post(CaseURLS.add_draft_update_request(app.pk), follow=True)
    update_request_pk = response.resolver_match.kwargs["update_request_pk"]

    resp = client.get(CaseURLS.edit_update_requests(app.pk, update_request_pk))
    assert resp.status_code == 200
    assertContains(resp, "You need to update your application with the following information")

    resp = client.post(CaseURLS.edit_update_requests(app.pk, update_request_pk), data=post)
    assert resp.status_code == 302
    assert app.update_requests.count() == 1

    app.refresh_from_db()
    assert app.status == ImportApplication.Statuses.PROCESSING

    return app.update_requests.first()


def test_list_update_requests_get(
    ilb_admin_client: Client,
    wood_app_submitted: ImportApplication,
):
    resp = ilb_admin_client.get(CaseURLS.list_update_requests(wood_app_submitted.pk))
    assert resp.status_code == 200

    assertContains(resp, "Wood (Quota) - Update Requests")
    assertTemplateUsed(resp, "web/domains/case/manage/update-requests/list.html")

    assert resp.context["previous_update_requests"].count() == 0
    assert resp.context["update_request"] is None


def test_manage_update_requests(ilb_admin_client: Client, wood_app_submitted: ImportApplication):
    post = {
        "request_subject": f"My Application update for {wood_app_submitted.reference}",
        "request_detail": "Please update your application",
        "send": "true",
    }
    update_request = get_open_update_request(ilb_admin_client, wood_app_submitted, post=post)
    check_gov_notify_email_was_sent(
        1,
        ["I1_main_contact@example.com"],  # /PS-IGNORE
        EmailTypes.APPLICATION_UPDATE,
        {
            "reference": wood_app_submitted.reference,
            "validate_digital_signatures_url": get_validate_digital_signatures_url(
                get_importer_site_domain()
            ),
            "application_url": get_case_view_url(wood_app_submitted, get_importer_site_domain()),
            "icms_url": get_importer_site_domain(),
            "service_name": SiteName.IMPORTER.label,
            "application_update_url": get_update_request_view_url(
                wood_app_submitted, update_request, get_importer_site_domain()
            ),
        },
        exp_subject=post["request_subject"],
        exp_in_body=post["request_detail"],
    )
    assert update_request.status == UpdateRequest.Status.OPEN


def test_start_update_request(
    importer_client: Client, ilb_admin_client: Client, wood_app_submitted: ImportApplication
):
    update_request = get_open_update_request(ilb_admin_client, wood_app_submitted)
    assert update_request.status == UpdateRequest.Status.OPEN

    resp = importer_client.post(
        CaseURLS.start_update_request(wood_app_submitted.pk, update_request.pk, "import"),
        data={},
    )
    assert resp.status_code == 302
    update_request.refresh_from_db()
    assert update_request.status == UpdateRequest.Status.UPDATE_IN_PROGRESS


def test_respond_update_request(
    importer_client: Client, ilb_admin_client: Client, wood_app_submitted: ImportApplication
):
    update_request = get_open_update_request(ilb_admin_client, wood_app_submitted)
    mail.outbox = []

    resp = importer_client.post(
        CaseURLS.start_update_request(wood_app_submitted.pk, update_request.pk, "import"),
        data={},
    )

    resp = importer_client.post(
        CaseURLS.respond_update_request(wood_app_submitted.pk, "import"),
        data={"response_detail": "fixed it"},
        follow=True,
    )
    assert resp.status_code == 200
    assert resp.resolver_match.view_name == "import:wood:edit"
    assert resp.resolver_match.kwargs["application_pk"] == wood_app_submitted.pk

    update_request.refresh_from_db()
    assert update_request.status == UpdateRequest.Status.UPDATE_IN_PROGRESS
    wood_app_submitted.refresh_from_db()
    assert wood_app_submitted.status == ImportApplication.Statuses.PROCESSING


def test_close_update_request_applicant_responded(
    importer_client: Client, ilb_admin_client: Client, wood_app_submitted: ImportApplication
):
    update_request = get_open_update_request(ilb_admin_client, wood_app_submitted)

    resp = importer_client.post(
        CaseURLS.start_update_request(wood_app_submitted.pk, update_request.pk, "import"),
        data={},
    )

    resp = importer_client.post(
        CaseURLS.respond_update_request(wood_app_submitted.pk, "import"),
        data={"response_detail": "fixed it"},
    )

    # Check submitted date time and last submitted date time match e.g. The application has not been updated
    original_date_time_submitted = wood_app_submitted.submit_datetime
    original_last_date_time_submitted = wood_app_submitted.last_submit_datetime
    assert original_date_time_submitted is not None
    assert original_date_time_submitted == original_last_date_time_submitted

    resubmit_app(
        client=importer_client, view_name="import:wood:submit-quota", app_pk=wood_app_submitted.pk
    )

    wood_app_submitted.refresh_from_db()

    # Check submitted date time and last submitted date time do not match e.g. The application has been updated
    assert original_date_time_submitted == wood_app_submitted.submit_datetime
    assert original_last_date_time_submitted != wood_app_submitted.last_submit_datetime

    resp = ilb_admin_client.post(
        CaseURLS.close_update_request(wood_app_submitted.pk, update_request.pk, "import"),
        data={},
    )

    assert resp.status_code == 302
    update_request.refresh_from_db()
    assert update_request.status == UpdateRequest.Status.CLOSED
    wood_app_submitted.refresh_from_db()
    assert wood_app_submitted.status == ImportApplication.Statuses.PROCESSING


def test_close_update_request_when_ilb_withdraws(
    importer_client: Client, ilb_admin_client: Client, wood_app_submitted: ImportApplication
):
    update_request = get_open_update_request(ilb_admin_client, wood_app_submitted)
    assert update_request.status == UpdateRequest.Status.OPEN

    # Empty the test outbox
    # calling get_open_update_request sends a EmailTypes.APPLICATION_UPDATE email.
    mail.outbox = []

    resp = ilb_admin_client.post(
        CaseURLS.close_update_request(wood_app_submitted.pk, update_request.pk, "import"),
        data={},
    )

    assert resp.status_code == 302
    update_request.refresh_from_db()
    assert update_request.status == UpdateRequest.Status.DRAFT

    check_gov_notify_email_was_sent(
        1,
        ["I1_main_contact@example.com"],  # /PS-IGNORE
        EmailTypes.APPLICATION_UPDATE_WITHDRAWN,
        {
            "reference": wood_app_submitted.reference,
            "validate_digital_signatures_url": get_validate_digital_signatures_url(
                get_importer_site_domain()
            ),
            "application_url": get_case_view_url(wood_app_submitted, get_importer_site_domain()),
            "icms_url": get_importer_site_domain(),
            "service_name": SiteName.IMPORTER.label,
        },
    )


def test_withdraw_update_request(
    importer_client: Client,
    ilb_admin_client: Client,
    wood_app_submitted: ImportApplication,
    ilb_admin_user: User,
) -> None:
    update_request = get_open_update_request(ilb_admin_client, wood_app_submitted)

    resp = ilb_admin_client.post(
        CaseURLS.close_update_request(wood_app_submitted.pk, update_request.pk, "import"),
        data={},
    )
    assert resp.status_code == 302

    update_request.refresh_from_db()

    assert update_request.status == UpdateRequest.Status.DRAFT
    assert update_request.is_active

    wood_app_submitted.refresh_from_db()
    assert wood_app_submitted.status == ImportApplication.Statuses.PROCESSING


def test_delete_draft_update_request(ilb_admin_client, fa_oil_app_submitted):
    assert fa_oil_app_submitted.update_requests.filter(is_active=True).count() == 0
    assert fa_oil_app_submitted.status == ImportApplication.Statuses.SUBMITTED

    ilb_admin_client.post(CaseURLS.take_ownership(fa_oil_app_submitted.pk))

    response = ilb_admin_client.post(
        CaseURLS.add_draft_update_request(fa_oil_app_submitted.pk), follow=True
    )
    update_request_pk = response.resolver_match.kwargs["update_request_pk"]

    assert fa_oil_app_submitted.update_requests.filter(is_active=True).count() == 1
    assert fa_oil_app_submitted.update_requests.first().status == UpdateRequest.Status.DRAFT

    response = ilb_admin_client.post(
        CaseURLS.delete_draft_update_request(fa_oil_app_submitted.pk, update_request_pk)
    )
    assert response.status_code == 302

    assert fa_oil_app_submitted.update_requests.filter(is_active=True).count() == 0
    assert fa_oil_app_submitted.update_requests.first().status == UpdateRequest.Status.DELETED
