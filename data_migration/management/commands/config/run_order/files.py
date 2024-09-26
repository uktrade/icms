from data_migration import models as dm
from data_migration import queries
from data_migration.management.commands.types import QueryModel

DEFAULT_FILE_CREATED_DATETIME = "2013-01-01 01:00:00"
DEFAULT_SECURE_LOB_REF_ID = 0

file_query_model = [
    QueryModel(
        queries.access_request_files,
        "Access Request Files",
        dm.AccessRequestFile,
        {
            "secure_lob_ref_id": DEFAULT_SECURE_LOB_REF_ID,
        },
    ),
]
