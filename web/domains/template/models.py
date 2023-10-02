from django.db import models

from web.models.mixins import Archivable
from web.types import TypedTextChoices

TEMPLATE_CONTENT_REGEX = r"\[\[{}\]\]"


class Template(Archivable, models.Model):
    # Template types
    ENDORSEMENT = "ENDORSEMENT"
    LETTER_TEMPLATE = "LETTER_TEMPLATE"
    EMAIL_TEMPLATE = "EMAIL_TEMPLATE"
    CFS_TRANSLATION = "CFS_TRANSLATION"
    DECLARATION = "DECLARATION"
    CFS_SCHEDULE = "CFS_SCHEDULE"
    LETTER_FRAGMENT = "LETTER_FRAGMENT"
    CFS_DECLARATION_TRANSLATION = "CFS_DECLARATION_TRANSLATION"
    CFS_SCHEDULE_TRANSLATION = "CFS_SCHEDULE_TRANSLATION"

    TYPES = (
        (ENDORSEMENT, "Endorsement"),
        (LETTER_TEMPLATE, "Letter template"),
        (EMAIL_TEMPLATE, "Email template"),
        (CFS_TRANSLATION, "CFS translation"),
        (DECLARATION, "Declaration"),
        (CFS_SCHEDULE, "CFS schedule"),
        (LETTER_FRAGMENT, "Letter fragment"),
        (CFS_DECLARATION_TRANSLATION, "CFS declaration translation"),
        (CFS_SCHEDULE_TRANSLATION, "CFS schedule translation"),
    )

    # Application domain
    CERTIFICATE_APPLICATION = "CA"
    IMPORT_APPLICATION = "IMA"
    ACCESS_REQUEST = "IAR"

    DOMAINS = (
        (CERTIFICATE_APPLICATION, "Certificate Applications"),
        (IMPORT_APPLICATION, "Import Applications"),
        (ACCESS_REQUEST, "Access Requests"),
    )

    # Template Status
    ACTIVE = True
    ARCHIVED = False

    STATUS = (
        (ACTIVE, "Active"),
        (ARCHIVED, "Archived"),
    )

    start_datetime = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    end_datetime = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(blank=False, null=False, default=True)
    template_name = models.CharField(max_length=100, blank=False, null=False)
    template_code = models.CharField(max_length=50, blank=True, null=True)
    template_type = models.CharField(max_length=50, choices=TYPES, blank=False, null=False)
    application_domain = models.CharField(max_length=20, choices=DOMAINS, blank=False, null=False)
    template_title = models.CharField(max_length=4000, blank=False, null=True)

    # everything except CFS schedules uses this; CFS schedules use "paragraphs" (see CFSScheduleParagraph, below)
    template_content = models.TextField(blank=False, null=True)

    countries = models.ManyToManyField("web.Country")
    country_translation_set = models.ForeignKey(
        "web.CountryTranslationSet", on_delete=models.SET_NULL, blank=False, null=True
    )

    @property
    def template_status(self):
        return "Active" if self.is_active else "Archived"

    @property
    def template_type_verbose(self):
        return dict(Template.TYPES)[self.template_type]

    @property
    def application_domain_verbose(self):
        return dict(Template.DOMAINS)[self.application_domain]

    def __str__(self):
        label = "Template"
        if self.id:
            return label + " - " + self.template_name
        else:
            return label

    class Meta:
        ordering = (
            "-is_active",
            "template_name",
        )


class CFSScheduleParagraph(models.Model):
    """Paragraphs for Certificate of Free Sale Schedule and Certificate of Free Sale Schedule Translation templates"""

    class ParagraphName(TypedTextChoices):
        SCHEDULE_HEADER = ("SCHEDULE_HEADER", "Schedule Header")
        SCHEDULE_INTRODUCTION = ("SCHEDULE_INTRODUCTION", "Schedule Introduction")
        IS_MANUFACTURER = ("IS_MANUFACTURER", "Is Manufacturer")
        IS_NOT_MANUFACTURER = ("IS_NOT_MANUFACTURER", "Is not Manufacturer")
        EU_COSMETICS_RESPONSIBLE_PERSON = (
            "EU_COSMETICS_RESPONSIBLE_PERSON",
            "EU Cosmetics Responsible Person",
        )
        EU_COSMETICS_RESPONSIBLE_PERSON_NI = (
            "EU_COSMETICS_RESPONSIBLE_PERSON_NI",
            "EU Cosmetics Responsible Person NI",
        )
        LEGISLATION_STATEMENT = ("LEGISLATION_STATEMENT", "Legislation Statement")
        ELIGIBILITY_ON_SALE = ("ELIGIBILITY_ON_SALE", "Eligibility on Sale")
        ELIGIBILITY_MAY_BE_SOLD = ("ELIGIBILITY_MAY_BE_SOLD", "Eligibility May Be Sold")
        GOOD_MANUFACTURING_PRACTICE = ("GOOD_MANUFACTURING_PRACTICE", "Good Manufacturing Practice")
        GOOD_MANUFACTURING_PRACTICE_NI = (
            "GOOD_MANUFACTURING_PRACTICE_NI",
            "Good Manufacturing Practice NI",
        )
        COUNTRY_OF_MAN_STATEMENT = ("COUNTRY_OF_MAN_STATEMENT", "Country of Manufacture Statement")
        COUNTRY_OF_MAN_STATEMENT_WITH_NAME = (
            "COUNTRY_OF_MAN_STATEMENT_WITH_NAME",
            "Country of Manufacture Statement With Name",
        )
        COUNTRY_OF_MAN_STATEMENT_WITH_NAME_AND_ADDRESS = (
            "COUNTRY_OF_MAN_STATEMENT_WITH_NAME_AND_ADDRESS",
            "Country of Manufacture Statement With Name and Address",
        )
        PRODUCTS = ("PRODUCTS", "Products")

    template = models.ForeignKey(
        "web.Template", on_delete=models.CASCADE, blank=False, null=False, related_name="paragraphs"
    )
    order = models.IntegerField(blank=False, null=False)
    name = models.CharField(max_length=100, blank=False, null=False, choices=ParagraphName.choices)
    content = models.TextField(blank=False, null=True)

    class Meta:
        ordering = ("order",)

        constraints = [models.UniqueConstraint(fields=["template", "name"], name="unique_name")]
