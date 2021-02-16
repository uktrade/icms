from django.db import models

from web.domains.constabulary.models import Constabulary
from web.domains.file.models import File
from web.domains.firearms.models import FirearmsAuthority
from web.domains.user.models import User

from ..models import ImportApplication


class OpenIndividualLicenceApplication(ImportApplication):
    PROCESS_TYPE = "OpenIndividualLicenceApplication"

    YES = "yes"
    NO = "no"
    KNOW_BOUGHT_FROM_CHOICES = (
        (YES, "Yes"),
        (NO, "No"),
    )

    section1 = models.BooleanField(verbose_name="Section 1", default=True)
    section2 = models.BooleanField(verbose_name="Section 2", default=True)
    know_bought_from = models.CharField(max_length=10, choices=KNOW_BOUGHT_FROM_CHOICES, null=True)


class ConstabularyEmail(models.Model):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    DRAFT = "DRAFT"
    STATUSES = ((OPEN, "Open"), (CLOSED, "Closed"), (DRAFT, "Draft"))

    is_active = models.BooleanField(blank=False, null=False, default=True)
    application = models.ForeignKey(
        ImportApplication, on_delete=models.PROTECT, blank=False, null=False
    )
    status = models.CharField(max_length=30, blank=False, null=False, default=DRAFT)
    email_cc_address_list = models.CharField(max_length=4000, blank=True, null=True)
    email_subject = models.CharField(max_length=100, blank=False, null=True)
    email_body = models.TextField(max_length=4000, blank=False, null=True)
    email_response = models.TextField(max_length=4000, blank=True, null=True)
    email_sent_datetime = models.DateTimeField(blank=True, null=True)
    email_closed_datetime = models.DateTimeField(blank=True, null=True)


class UserImportCertificate(models.Model):
    REGISTERED_KEY = "registered"
    REGISTERED_TEXT = "Registered Firearms Dealer Certificate"
    REGISTERED = (REGISTERED_KEY, REGISTERED_TEXT)
    CERTIFICATE_TYPE = (
        ("firearms", "Firearms Certificate"),
        REGISTERED,
        ("shotgun", "Shotgun Certificate"),
    )

    import_application = models.ForeignKey(ImportApplication, on_delete=models.PROTECT)
    reference = models.CharField(verbose_name="Certificate Reference", max_length=200)
    certificate_type = models.CharField(
        verbose_name="Certificate Type", choices=CERTIFICATE_TYPE, max_length=200
    )
    constabulary = models.ForeignKey(Constabulary, on_delete=models.PROTECT)
    date_issued = models.DateField(verbose_name="Date Issued")
    expiry_date = models.DateField(verbose_name="Expiry Date")
    files = models.ManyToManyField(File)

    created_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now=True)


class VerifiedCertificate(models.Model):
    import_application = models.ForeignKey(
        ImportApplication, on_delete=models.PROTECT, related_name="verified_certificates"
    )
    firearms_authority = models.ForeignKey(
        FirearmsAuthority, on_delete=models.PROTECT, related_name="+"
    )

    created_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now=True)


class WithdrawImportApplication(models.Model):
    STATUS_OPEN = "open"
    STATUSES = (
        (STATUS_OPEN, "OPEN"),
        ("rejected", "REJECTED"),
        ("accepted", "ACCEPTED"),
    )
    import_application = models.ForeignKey(
        ImportApplication, on_delete=models.PROTECT, related_name="withdrawals"
    )
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=10, choices=STATUSES, default=STATUS_OPEN)
    reason = models.TextField()
    request_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="+",
    )

    response = models.TextField()
    response_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="+",
    )

    created_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now=True)


class ChecklistFirearmsOILApplication(models.Model):
    CHOICES = (
        ("yes", "Yes"),
        ("no", "No"),
        ("n/a", "N/A"),
    )
    import_application = models.ForeignKey(
        OpenIndividualLicenceApplication, on_delete=models.PROTECT, related_name="checklists"
    )
    authority_required = models.CharField(
        max_length=10,
        choices=CHOICES,
        blank=True,
        null=True,
        verbose_name="Authority to possess required?",
    )
    authority_received = models.CharField(
        max_length=10,
        choices=CHOICES,
        blank=True,
        null=True,
        verbose_name="Authority to possess received?",
    )
    authority_police = models.CharField(
        max_length=10,
        choices=CHOICES,
        blank=True,
        null=True,
        verbose_name="Authority to possess checked with police?",
    )
    case_update = models.CharField(
        max_length=10,
        choices=CHOICES,
        blank=True,
        null=True,
        verbose_name="Case update required from applicant?",
    )
    fir_required = models.CharField(
        max_length=10,
        choices=CHOICES,
        blank=True,
        null=True,
        verbose_name="Further information request required?",
    )
    response_preparation = models.BooleanField(
        default=False,
        verbose_name="Response Preparation - approve/refuse the request, edit details if necessary",
    )
    validity_match = models.CharField(
        max_length=10,
        choices=CHOICES,
        blank=True,
        null=True,
        verbose_name="Validity period of licence matches that of the RFD certificate?",
    )
    endorsements_listed = models.CharField(
        max_length=10,
        choices=CHOICES,
        blank=True,
        null=True,
        verbose_name="Correct endorsements listed? Add/edit/remove as required (changes are automatically saved)",
    )
    authorisation = models.BooleanField(
        default=False,
        verbose_name="Authorisation - start authorisation (close case processing) to authorise the licence. Errors logged must be resolved.",
    )
