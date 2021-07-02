from django.db import models

from web.domains.case._import.models import ImportApplication, ImportApplicationType
from web.domains.file.models import File


class TextilesApplication(ImportApplication):
    PROCESS_TYPE = ImportApplicationType.ProcessTypes.TEXTILES

    # TODO: add other fields

    #  supporting documents
    supporting_documents = models.ManyToManyField(File, related_name="+")
