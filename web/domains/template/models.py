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
    template_type = models.CharField(max_length=20,
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

    class Meta:
        ordering = ('-is_active', )

    # Default display fields on the listing page of the model
    class Display:
        display = [
            'template_name', 'application_domain_verbose',
            'template_type_verbose', 'template_status'
        ]
        labels = [
            'Template Name', 'Application Domain', 'Template Type',
            'Template Status'
        ]
        #  Display actions
        edit = True
        view = True
        archive = True
