from django.db import connections
from django.db.models import Model, sql

# Based on answer in
# https://stackoverflow.com/questions/65420783/bulk-create-with-multi-table-inheritance-models


def bulk_create(model: Model, items: list[Model], db: str = "default") -> None:
    """Custom bulk create to allow bulk create for table inheritance

    :param model: The model being created
    :param items: A list of new models populated with data
    :param db: The database being targeted
    """

    connection = connections[db]
    fields = model._meta.local_concrete_fields
    query = sql.InsertQuery(model)
    query.insert_values(fields, items)
    query.get_compiler(connection=connection).execute_sql()
    # TODO: Increment the sequence so autoincrement will work after running
