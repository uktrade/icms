from django.db import models

from web.domains.case._import.models import ImportApplication, ImportApplicationType
from web.domains.file.models import File


class PriorSurveillanceApplication(ImportApplication):
    PROCESS_TYPE = ImportApplicationType.ProcessTypes.SPS

    # TODO: add other fields

    #  supporting documents
    supporting_documents = models.ManyToManyField(File, related_name="+")
