from data_migration import queries

GROUPS_TO_ROLES = {
    "Importer User": queries.importer_user_roles,
    "Exporter User": queries.exporter_user_roles,
    "ILB Case Officer": queries.ilb_user_roles,
    "Home Office Case Officer": queries.home_office_user_roles,
    "NCA Case Officer": queries.nca_user_roles,
    "Constabulary Contact": queries.constabulary_user_roles,
    "Import Search User": queries.import_search_user_roles,
}
