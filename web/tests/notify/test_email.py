import pytest
from django.core import mail
from django.test import TestCase

from web.models import AlternativeEmail, PersonalEmail, User, WithdrawApplication
from web.notify import constants, email
from web.tests.helpers import (
    CaseURLS,
    add_variation_request_to_app,
    check_email_was_sent,
)


class TestEmail(TestCase):
    def create_user_emails(self, members=None):
        if not members:
            members = []

        for member in members:
            user = User.objects.get(username=member["username"])

            for m in member.get("personal", []):
                PersonalEmail(user=user, email=m["email"], portal_notifications=m["notify"]).save()
            if "alternative" in member:
                for m in member.get("alternative", []):
                    AlternativeEmail(
                        user=user, email=m["email"], portal_notifications=m["notify"]
                    ).save()

    def setup_user_emails(self):
        # An active import organisation
        self.create_user_emails(
            members=[
                {
                    "username": "I1_main_contact",
                    "personal": [
                        {
                            "email": "I1_main_contact_second_email@example.com",  # /PS-IGNORE
                            "notify": True,
                        },
                        {
                            "email": "I1_main_contact_no_notify@example.com",  # /PS-IGNORE
                            "notify": False,
                        },
                    ],
                    "alternative": [
                        {"email": "I1_main_contact_alt@example.com", "notify": True},  # /PS-IGNORE
                        {
                            "email": "I1_main_contact_alt_no_notify@example.com",  # /PS-IGNORE
                            "notify": False,
                        },
                    ],
                },
                {
                    "username": "I1_A1_main_contact",
                    "alternative": [
                        {
                            "email": "I1_A1_main_contact_alt@example.com",  # /PS-IGNORE
                            "notify": True,
                        }
                    ],
                },
                {
                    "username": "I3_inactive_contact",
                    "alternative": [
                        {
                            "email": "I3_inactive_contact_alt@example.com",  # /PS-IGNORE
                            "notify": True,
                        }
                    ],
                },
                {
                    "username": "E1_main_contact",
                    "personal": [
                        {
                            "email": "E1_main_contact_second_email@example.com",  # /PS-IGNORE
                            "notify": True,
                        },
                        {
                            "email": "E1_main_contact_no_notify@example.com",  # /PS-IGNORE
                            "notify": False,
                        },
                    ],
                    "alternative": [
                        {
                            "email": "E1_main_contact_alt@example.com",  # /PS-IGNORE
                            "notify": True,
                        },
                        {
                            "email": "E1_main_contact_alt_no_notify@example.com",  # /PS-IGNORE
                            "notify": False,
                        },
                    ],
                },
                {
                    "username": "E1_A1_main_contact",
                    "alternative": [
                        {
                            "email": "E1_A1_main_contact_alt@example.com",  # /PS-IGNORE
                            "notify": True,
                        },
                        {
                            "email": "E1_A1_main_contact_alt_no_notify@example.com",  # /PS-IGNORE
                            "notify": False,
                        },
                    ],
                },
                {
                    "username": "E3_inactive_contact",
                    "alternative": [
                        {
                            "email": "archived_export_user_alt@example.com",  # /PS-IGNORE
                            "notify": True,
                        }
                    ],
                },
            ],
        )

    def setUp(self):
        self.setup_user_emails()

    def test_send_email(self):
        email.send_email.delay(
            "Test subject",
            "Test message",
            ["test@example.com", "test2@example.com"],  # /PS-IGNORE
            html_message="<p>Test message</p>",
        )
        outbox = mail.outbox
        assert len(outbox) == 1
        assert "test@example.com" in outbox[0].to  # /PS-IGNORE
        assert "test2@example.com" in outbox[0].to  # /PS-IGNORE

    def test_multipart_email(self):
        email.send_email("Subject", "Message", ["test@example.com", "<p>Message</p>"])  # /PS-IGNORE
        m = mail.outbox[0]
        assert isinstance(m, mail.EmailMultiAlternatives)

    def test_mail_subject(self):
        email.send_email("Subject", "Message", ["test@example.com", "<p>Message</p>"])  # /PS-IGNORE
        m = mail.outbox[0]
        assert m.subject == "Subject"

    def test_mail_body(self):
        email.send_email("Subject", "Message", ["test@example.com", "<p>Message</p>"])  # /PS-IGNORE
        m = mail.outbox[0]
        assert m.body == "Message"

    def test_mail_from(self):
        email.send_email("Subject", "Message", ["test@example.com", "<p>Message</p>"])  # /PS-IGNORE
        m = mail.outbox[0]

        # Set in config/settings/non_prod_base.py
        assert m.from_email == "enquiries.ilb@icms.trade.dev.uktrade.io"  # /PS-IGNORE

    def test_mail_to(self):
        email.send_email(
            "Subject",
            "Message",
            ["test@example.com", "test2@example.com", "<p>Message</p>"],  # /PS-IGNORE
        )
        m = mail.outbox[0]
        assert m.to[0] == "test@example.com"  # /PS-IGNORE
        assert m.to[1] == "test2@example.com"  # /PS-IGNORE

    def test_send_mailshot_to_importers(self):
        email.send_mailshot.delay(
            "Test subject", "Test message", html_message="<p>Test message</p>", to_importers=True
        )
        outbox = mail.outbox
        assert len(outbox) == 3
        # Many-to-many relations order is not guaranteed
        # Members of exporter team might have different order
        # Testing by length
        for o in outbox:
            if len(o.to) == 3:
                assert "I1_main_contact@example.com" in o.to  # /PS-IGNORE
                assert "I1_main_contact_second_email@example.com" in o.to  # /PS-IGNORE
                assert "I1_main_contact_alt@example.com" in o.to  # /PS-IGNORE
            elif len(o.to) == 2:
                assert "I1_A1_main_contact@example.com" in o.to  # /PS-IGNORE
                assert "I1_A1_main_contact_alt@example.com" in o.to  # /PS-IGNORE
            elif len(o.to) == 1:
                assert "I2_main_contact@example.com" in o.to  # /PS-IGNORE
            else:
                raise AssertionError(f"Test failed with invalid email recipients {str(o.to)}")

    def test_send_mailshot_to_exporters(self):
        email.send_mailshot.delay(
            "Test subject", "Test message", html_message="<p>Test message</p>", to_exporters=True
        )
        outbox = mail.outbox
        assert len(outbox) == 3
        # Many-to-many relations order is not guaranteed
        # Members of exporter team might have different order
        # Testing by length
        for o in outbox:
            if len(o.to) == 3:
                assert "E1_main_contact@example.com" in o.to  # /PS-IGNORE
                assert "E1_main_contact_second_email@example.com" in o.to  # /PS-IGNORE
                assert "E1_main_contact_alt@example.com" in o.to  # /PS-IGNORE
            elif len(o.to) == 2:
                assert "E1_A1_main_contact@example.com" in o.to  # /PS-IGNORE
                assert "E1_A1_main_contact_alt@example.com" in o.to  # /PS-IGNORE
            elif len(o.to) == 1:
                assert "E2_main_contact@example.com" in o.to  # /PS-IGNORE
            else:
                raise AssertionError(f"Test failed with invalid email recipients {str(o.to)}")


@pytest.mark.django_db
def test_send_to_application_contacts_import(fa_sil_app_submitted):
    email.send_to_application_contacts(fa_sil_app_submitted, "Test", "Test Body")
    outbox = mail.outbox
    assert len(outbox) == 1

    o = outbox[0]
    assert o.to == ["I1_main_contact@example.com"]  # /PS-IGNORE
    assert o.subject == "Test"
    assert o.body == "Test Body"


@pytest.mark.django_db
def test_send_to_application_agent_import(fa_sil_app_submitted, agent_importer):
    fa_sil_app_submitted.agent = agent_importer
    email.send_to_application_contacts(fa_sil_app_submitted, "Test", "Test Body")
    outbox = mail.outbox

    assert len(outbox) == 1
    o = outbox[0]
    assert o.to == ["I1_A1_main_contact@example.com"]  # /PS-IGNORE
    assert o.subject == "Test"
    assert o.body == "Test Body"


@pytest.mark.django_db
def test_send_to_application_contacts_export(com_app_submitted):
    email.send_to_application_contacts(com_app_submitted, "Test", "Test Body")
    outbox = mail.outbox
    assert len(outbox) == 1

    o = outbox[0]
    assert o.to == ["E1_main_contact@example.com"]  # /PS-IGNORE
    assert o.subject == "Test"
    assert o.body == "Test Body"


@pytest.mark.django_db
def test_send_to_application_agent_export(com_app_submitted, agent_exporter):
    com_app_submitted.agent = agent_exporter
    com_app_submitted.save()
    email.send_to_application_contacts(com_app_submitted, "Test", "Test Body")
    outbox = mail.outbox

    assert len(outbox) == 1
    o = outbox[0]
    assert o.to == ["E1_A1_main_contact@example.com"]  # /PS-IGNORE
    assert o.subject == "Test"
    assert o.body == "Test Body"


def test_send_refused_email_import(complete_rejected_app):
    _check_send_refused_email(complete_rejected_app, "I1_main_contact@example.com")  # /PS-IGNORE


def test_send_refused_email_export(complete_rejected_export_app):
    _check_send_refused_email(
        complete_rejected_export_app, "E1_main_contact@example.com"  # /PS-IGNORE
    )


def _check_send_refused_email(app, expected_to_email):
    outbox = mail.outbox

    assert len(outbox) == 1
    first_email = outbox[0]
    assert first_email.to == [expected_to_email]
    assert first_email.subject == f"Application reference {app.reference} has been refused by ILB."
    assert "has been refused by ILB" in first_email.body
    assert app.refuse_reason in first_email.body


def test_send_database_email(com_app_submitted):
    email.send_database_email(com_app_submitted, constants.DatabaseEmailTemplate.STOP_CASE)
    outbox = mail.outbox
    assert len(outbox) == 1

    sent_email = outbox[0]
    assert sent_email.to == ["E1_main_contact@example.com"]  # /PS-IGNORE
    assert sent_email.subject == f"ICMS Case Reference {com_app_submitted.reference} Stopped"
    assert (
        f"Processing on ICMS Case Reference {com_app_submitted.reference} has been stopped"
    ) in sent_email.body


def test_send_reassign_email(ilb_admin_client, fa_sil_app_submitted):
    app = fa_sil_app_submitted
    ilb_admin_client.post(CaseURLS.take_ownership(app.pk))
    app.refresh_from_db()
    email.send_reassign_email(app, "")
    outbox = mail.outbox

    assert len(outbox) == 1

    m = outbox[0]

    assert m.to == ["ilb_admin_user@example.com"]  # /PS-IGNORE
    assert m.subject == f"ICMS Case Ref. {app.reference} has been assigned to you"
    assert f"ICMS Case Ref. { app.reference } has been assigned to you." in m.body
    assert "Handover Details" not in m.body


def test_send_reassign_email_with_comment(ilb_admin_client, fa_sil_app_submitted):
    app = fa_sil_app_submitted
    ilb_admin_client.post(CaseURLS.take_ownership(app.pk))
    app.refresh_from_db()
    email.send_reassign_email(app, "Some comment")
    outbox = mail.outbox

    assert len(outbox) == 1

    m = outbox[0]

    assert m.to == ["ilb_admin_user@example.com"]  # /PS-IGNORE
    assert m.subject == f"ICMS Case Ref. {app.reference} has been assigned to you"
    assert f"ICMS Case Ref. { app.reference } has been assigned to you." in m.body
    assert "Handover Details" in m.body
    assert "Some comment" in m.body


@pytest.mark.parametrize(
    "withdrawal_status,exp_num_emails,exp_subject,exp_in_body,exp_sent_to",
    [
        (
            WithdrawApplication.Statuses.OPEN,
            2,
            "Withdrawal Request: ",
            "A withdrawal request has been submitted",
            "ilb_admin_user@example.com",  # /PS-IGNORE
        ),
        (
            WithdrawApplication.Statuses.ACCEPTED,
            1,
            "Withdrawal Request Accepted: ",
            "This case has\nbeen withdrawn.",
            "E1_main_contact@example.com",  # /PS-IGNORE
        ),
        (
            WithdrawApplication.Statuses.REJECTED,
            1,
            "Withdrawal Request Rejected: ",  # /PS-IGNORE
            "has been rejected for the\nfollowing reason:",
            "E1_main_contact@example.com",  # /PS-IGNORE
        ),
        (
            WithdrawApplication.Statuses.DELETED,
            2,
            "Withdrawal Request Cancelled: ",
            "has been cancelled.",
            "ilb_admin_user@example.com",  # /PS-IGNORE
        ),
    ],
)
def test_send_withdrawal_email(
    com_app_submitted,
    importer_one_contact,
    withdrawal_status,
    exp_num_emails,
    exp_subject,
    exp_in_body,
    exp_sent_to,
):
    withdrawal = com_app_submitted.withdrawals.create(
        status=withdrawal_status, request_by=importer_one_contact
    )

    email.send_withdrawal_email(withdrawal)
    exp_subject = f"{exp_subject}{com_app_submitted.reference}"
    check_email_was_sent(exp_num_emails, exp_sent_to, exp_subject, exp_in_body)


def test_send_withdrawal_email_with_unsupported_status(com_app_submitted, importer_one_contact):
    withdrawal = com_app_submitted.withdrawals.create(
        status="TEST", request_by=importer_one_contact
    )
    with pytest.raises(ValueError) as e_info:
        email.send_withdrawal_email(withdrawal)
        assert e_info == "Unsupported Variation Request Description"


@pytest.mark.parametrize(
    "desc,exp_num_emails,exp_subject,exp_in_body,exp_sent_to",
    [
        (
            constants.VariationRequestDescription.CANCELLED,
            1,
            "Variation Request Cancelled",
            "has been cancelled",
            "ilb_admin_user@example.com",  # /PS-IGNORE
        ),
        (
            constants.VariationRequestDescription.UPDATE_REQUIRED,
            1,
            "Variation Update Required",
            "needs updating",
            "I1_main_contact@example.com",  # /PS-IGNORE
        ),
        (
            constants.VariationRequestDescription.UPDATE_CANCELLED,
            1,
            "Variation Update No Longer Required",
            "no longer requires\nan update",
            "I1_main_contact@example.com",  # /PS-IGNORE
        ),
        (
            constants.VariationRequestDescription.REFUSED,
            1,
            "Variation on application reference IMA/2023/00001 has been refused by ILB",
            "has been refused by\nILB",
            "I1_main_contact@example.com",  # /PS-IGNORE
        ),
        (
            constants.VariationRequestDescription.UPDATE_RECEIVED,
            1,
            "Variation Update Received",
            "A variation update has been received for ICMS application",
            "ilb_admin_two@example.com",  # /PS-IGNORE
        ),
    ],
)
def test_send_variation_request_email(
    fa_oil_app_submitted,
    ilb_admin_user,
    ilb_admin_two,
    desc,
    exp_num_emails,
    exp_subject,
    exp_in_body,
    exp_sent_to,
):
    fa_oil_app_submitted.case_owner = ilb_admin_two
    fa_oil_app_submitted.save()
    vr = add_variation_request_to_app(fa_oil_app_submitted, ilb_admin_user)
    email.send_variation_request_email(vr, desc, fa_oil_app_submitted)
    check_email_was_sent(exp_num_emails, exp_sent_to, exp_subject, exp_in_body)


def test_send_variation_request_email_with_unsupported_description(
    com_app_submitted, ilb_admin_user
):
    vr = add_variation_request_to_app(com_app_submitted, ilb_admin_user)
    with pytest.raises(ValueError) as e_info:
        email.send_variation_request_email(vr, "TEST", com_app_submitted)
        assert e_info == "Unsupported Variation Request Description"


def test_send_application_update_response_email(com_app_submitted, ilb_admin_two):
    com_app_submitted.case_owner = ilb_admin_two
    email.send_application_update_reponse_email(com_app_submitted)
    check_email_was_sent(
        1,
        ilb_admin_two.email,
        f"Application Update Response - {com_app_submitted.reference}",
        "An application update response has been submitted for case",
    )
