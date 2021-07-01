from web.domains.case._import.models import ImportApplication, ImportApplicationType


class TextilesApplication(ImportApplication):
    PROCESS_TYPE = ImportApplicationType.ProcessTypes.TEXTILES

    # TODO: add other fields
