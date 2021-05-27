from django.db import models

from web.domains.constabulary.models import Constabulary
from web.domains.file.models import File
from web.domains.firearms.models import FirearmsAuthority

from ..models import ImportApplication


class UserImportCertificate(File):
    """User imported certificates."""

    class CertificateType(models.TextChoices):
        firearms = ("firearms", "Firearms Certificate")
        registered = ("registered", "Registered Firearms Dealer Certificate")
        shotgun = ("shotgun", "Shotgun Certificate")

        @classmethod
        def registered_as_choice(cls):
            return (cls.registered.value, cls.registered.label)

    reference = models.CharField(verbose_name="Certificate Reference", max_length=200)
    certificate_type = models.CharField(
        verbose_name="Certificate Type", choices=CertificateType.choices, max_length=200
    )
    constabulary = models.ForeignKey(Constabulary, on_delete=models.PROTECT)
    date_issued = models.DateField(verbose_name="Date Issued")
    expiry_date = models.DateField(verbose_name="Expiry Date")
    updated_datetime = models.DateTimeField(auto_now=True)


class OpenIndividualLicenceApplication(ImportApplication):
    PROCESS_TYPE = "OpenIndividualLicenceApplication"

    section1 = models.BooleanField(verbose_name="Section 1", default=True)
    section2 = models.BooleanField(verbose_name="Section 2", default=True)

    know_bought_from = models.BooleanField(null=True)
    user_imported_certificates = models.ManyToManyField(
        UserImportCertificate, related_name="import_application"
    )

    commodity_code = models.CharField(max_length=40, blank=False, null=True)


class ConstabularyEmail(models.Model):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    DRAFT = "DRAFT"
    STATUSES = ((OPEN, "Open"), (CLOSED, "Closed"), (DRAFT, "Draft"))

    is_active = models.BooleanField(blank=False, null=False, default=True)

    application = models.ForeignKey(
        OpenIndividualLicenceApplication,
        on_delete=models.PROTECT,
        related_name="constabulary_emails",
        blank=False,
        null=False,
    )
    status = models.CharField(max_length=30, blank=False, null=False, default=DRAFT)
    email_to = models.CharField(max_length=4000, blank=True, null=True)
    email_cc_address_list = models.CharField(max_length=4000, blank=True, null=True)
    email_subject = models.CharField(max_length=100, blank=False, null=True)
    email_body = models.TextField(max_length=4000, blank=False, null=True)
    email_response = models.TextField(max_length=4000, blank=True, null=True)
    email_sent_datetime = models.DateTimeField(blank=True, null=True)
    email_closed_datetime = models.DateTimeField(blank=True, null=True)
    attachments = models.ManyToManyField(File)

    @property
    def is_draft(self):
        return self.status == self.DRAFT


class VerifiedCertificate(models.Model):
    import_application = models.ForeignKey(
        OpenIndividualLicenceApplication,
        on_delete=models.PROTECT,
        related_name="verified_certificates",
    )
    firearms_authority = models.ForeignKey(
        FirearmsAuthority, on_delete=models.PROTECT, related_name="verified_certificates"
    )

    created_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now=True)


# FIXME: Refactor to use base class
class ChecklistFirearmsOILApplication(models.Model):
    import_application = models.ForeignKey(
        OpenIndividualLicenceApplication, on_delete=models.PROTECT, related_name="checklists"
    )

    class Response(models.TextChoices):
        yes = ("yes", "Yes")
        no = ("no", "No")
        not_applicable = ("n/a", "N/A")

    authority_required = models.CharField(
        max_length=10,
        choices=Response.choices,
        blank=True,
        null=True,
        verbose_name="Authority to possess required?",
    )
    authority_received = models.CharField(
        max_length=10,
        choices=Response.choices,
        blank=True,
        null=True,
        verbose_name="Authority to possess received?",
    )
    authority_police = models.CharField(
        max_length=10,
        choices=Response.choices,
        blank=True,
        null=True,
        verbose_name="Authority to possess checked with police?",
    )
    case_update = models.CharField(
        max_length=10,
        choices=Response.choices,
        blank=True,
        null=True,
        verbose_name="Case update required from applicant?",
    )
    fir_required = models.CharField(
        max_length=10,
        choices=Response.choices,
        blank=True,
        null=True,
        verbose_name="Further information request required?",
    )
    response_preparation = models.BooleanField(
        default=False,
        verbose_name="Response Preparation - approve/refuse the request, edit details if necessary",
    )
    # FIXME: Rename Has different db name and verbose name (validity_period_correct & "Validity period correct?")
    validity_match = models.CharField(
        max_length=10,
        choices=Response.choices,
        blank=True,
        null=True,
        verbose_name="Validity period of licence matches that of the RFD certificate?",
    )
    endorsements_listed = models.CharField(
        max_length=10,
        choices=Response.choices,
        blank=True,
        null=True,
        verbose_name="Correct endorsements listed? Add/edit/remove as required (changes are automatically saved)",
    )
    authorisation = models.BooleanField(
        default=False,
        verbose_name="Authorisation - start authorisation (close case processing) to authorise the licence. Errors logged must be resolved.",
    )
