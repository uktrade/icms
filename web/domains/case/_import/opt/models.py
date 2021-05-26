from django.db import models

from web.domains.file.models import File

from ..models import ImportApplication


class OutwardProcessingTradeApplication(ImportApplication):
    PROCESS_TYPE = "OutwardProcessingTradeApplication"

    # TODO: ICMSLST-593 add data for this application type

    supporting_documents = models.ManyToManyField(File, related_name="+")
