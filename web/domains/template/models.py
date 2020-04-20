import re

from django.db import models

from web.domains.country.models import Country, CountryTranslationSet
from web.models.mixins import Archivable


class Template(Archivable, models.Model):

    # Template types
    ENDORSEMENT = 'ENDORSEMENT'
    LETTER_TEMPLATE = 'LETTER_TEMPLATE'
    EMAIL_TEMPLATE = 'EMAIL_TEMPLATE'
    CFS_TRANSLATION = 'CFS_TRANSLATION'
    DECLARATION = 'DECLARATION'
    CFS_SCHEDULE = 'CFS_SCHEDULE'
    LETTER_FRAGMENT = 'LETTER_FRAGMENT'
    CFS_DECLARATION_TRANSLATION = 'CFS_DECLARATION_TRANSLATION'
    CFS_SCHEDULE_TRANSLATION = 'CFS_SCHEDULE_TRANSLATION'

    TYPES = (
        (ENDORSEMENT, 'Endorsement'),
        (LETTER_TEMPLATE, 'Letter template'),
        (EMAIL_TEMPLATE, 'Email template'),
        (CFS_TRANSLATION, 'CFS translation'),
        (DECLARATION, 'Declaration'),
        (CFS_SCHEDULE, 'CFS schedule'),
        (LETTER_FRAGMENT, 'Letter fragment'),
        (CFS_DECLARATION_TRANSLATION, 'CFS declaration translation'),
        (CFS_SCHEDULE_TRANSLATION, 'CFS schedule translation'),
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

    start_datetime = models.DateTimeField(auto_now_add=True,
                                          blank=False,
                                          null=False)
    end_datetime = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(blank=False, null=False, default=True)
    template_name = models.CharField(max_length=100, blank=False, null=False)
    template_code = models.CharField(max_length=50, blank=True, null=True)
    template_type = models.CharField(max_length=50,
                                     choices=TYPES,
                                     blank=False,
                                     null=False)
    application_domain = models.CharField(max_length=20,
                                          choices=DOMAINS,
                                          blank=False,
                                          null=False)
    template_title = models.CharField(max_length=4000, blank=False, null=True)
    template_content = models.TextField(blank=False, null=True)
    countries = models.ManyToManyField(Country)
    country_translation_set = models.ForeignKey(CountryTranslationSet,
                                                on_delete=models.SET_NULL,
                                                blank=False,
                                                null=True)

    @property
    def template_status(self):
        return 'Active' if self.is_active else 'Archived'

    @property
    def template_type_verbose(self):
        return dict(Template.TYPES)[self.template_type]

    @property
    def application_domain_verbose(self):
        return dict(Template.DOMAINS)[self.application_domain]

    def __str__(self):
        label = 'Template'
        if self.id:
            return label + ' - ' + self.template_name
        else:
            return label

    def get_content(self, replacements={}):
        """
        returns the template content with the placeholders replaced with their value

        calling this function with replacements={'foo': 'bar'} will return the template content
        with all occurences of [[foo]] replaced with bar
        """
        content = self.template_content

        if content is None:
            return ""

        for replacement, value in replacements.items():
            content = re.sub(r"\[\[%s\]\]" % replacement, value, content)

        return content

    @staticmethod
    def get_choice_entry(items, search):
        """
            Returns the entry that matched the `search` term on the `items` collection
            This is meant to be used to create form that need a choice with only a few of the
            configured choices

            e.g: Template.get_choice_entry(Template.DOMAINS, Template.IMPORT_APPLICATION)
            returns  (IMPORT_APPLICATION, "Import Applications")
        """
        for entry in items:
            if entry[0] == search:
                return entry

    class Meta:
        ordering = (
            '-is_active',
            'template_name',
        )


class CFSScheduleTranslationParagraph(models.Model):
    """
        Paragraphs for Certificate of Free Sale Schedule and
        Certificate of Free Sale Schedule Translation templates
    """
    template = models.ForeignKey(Template,
                                 on_delete=models.CASCADE,
                                 blank=False,
                                 null=False,
                                 related_name='paragraphs')
    order = models.IntegerField(blank=False, null=False)
    name = models.CharField(max_length=100, blank=False, null=False)
    content = models.TextField(blank=False, null=True)

    class Meta:
        ordering = ('order',)
