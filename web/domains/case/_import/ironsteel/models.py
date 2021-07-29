from web.domains.case._import.models import ImportApplication, ImportApplicationType


class IronSteelApplication(ImportApplication):
    PROCESS_TYPE = ImportApplicationType.ProcessTypes.IRON_STEEL

    # TODO: add other fields
