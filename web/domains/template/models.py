import re
from django.db import models
from web.models.mixins import Archivable


class Template(Archivable, models.Model):

    # Template types
    ENDORSEMENT = 'ENDORSEMENT'
    LETTER_TEMPLATE = 'LETTER_TEMPLATE'
    EMAIL_TEMPLATE = 'EMAIL_TEMPLATE'
    CFS_TRANSLATION = 'CFS_TRANSLATION'
    DECLARATION = 'DECLARATION'

    TYPES = (
        (ENDORSEMENT, 'Endorsement'),
        (LETTER_TEMPLATE, 'Letter template'),
        (EMAIL_TEMPLATE, 'Email template'),
        (CFS_TRANSLATION, 'CFS translation'),
        (DECLARATION, 'Declaration'),
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

    start_datetime = models.DateTimeField(blank=False, null=False)
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
        for replacement, value in replacements.items():
            content = re.sub(r"\[\[%s\]\]" % replacement, value, content)

        return content

    class Meta:
        ordering = (
            '-is_active',
            'template_name',
        )
