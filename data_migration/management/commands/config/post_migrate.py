from data_migration import queries
from data_migration.management.commands._types import ModelReference
from web.models import AccessRequest, ExportApplication, ImportApplication, Mailshot

GROUPS_TO_ROLES = {
    "Importer User": queries.importer_user_roles,
    "Exporter User": queries.exporter_user_roles,
    "ILB Case Officer": queries.ilb_user_roles,
    "Home Office Case Officer": queries.home_office_user_roles,
    "NCA Case Officer": queries.nca_user_roles,
    "Constabulary Contact": queries.constabulary_user_roles,
    "Import Search User": queries.import_search_user_roles,
}


MODEL_REFERENCES: dict[str, ModelReference] = {
    "access": ModelReference(
        model=AccessRequest, filter_params={"reference__isnull": False}, year=False
    ),
    "export": ModelReference(model=ExportApplication, filter_params={"reference__isnull": False}),
    "import": ModelReference(
        model=ImportApplication,
        filter_params={"reference__isnull": False, "legacy_case_flag": False},
    ),
    "mailshot": ModelReference(
        model=Mailshot, filter_params={"reference__isnull": False}, year=False
    ),
}
