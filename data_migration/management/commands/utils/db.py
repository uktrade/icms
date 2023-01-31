from django.conf import settings
from django.db import connections, transaction
from django.db.models import Model, sql

from data_migration.models import Process

CONNECTION_CONFIG = {
    "user": settings.ICMS_V1_REPLICA_USER,
    "password": settings.ICMS_V1_REPLICA_PASSWORD,
    "dsn": settings.ICMS_V1_REPLICA_DSN,
}


set_seq_sql = """
SELECT
  setval(pg_get_serial_sequence('"{table_name}"','{pk_column}')
  , coalesce(max("{pk_column}"), 1), max("{pk_column}") IS NOT null)
FROM "{table_name}";
"""


def bulk_create(model: Model, objs: list[Model]) -> None:
    """Custom bulk create to allow bulk create for table inheritance and when specifying id

    When passing ids to Model.objects.bulk_create in postgres, the sequence is not updated
    automatically so requires being manually set. This would likely cause a race condition
    if used at the same time as creating db objects in the system, so must only be used for
    the data migration prior to going live.

    :param model: The model being created
    :param items: A list of new models populated with data
    :param db: The database being targeted
    """

    db = model.objects.db

    with transaction.atomic(using=db, savepoint=False):
        connection = connections[db]
        fields = model._meta.local_concrete_fields
        query = sql.InsertQuery(model)
        query.insert_values(fields, objs)
        query.get_compiler(connection=connection).execute_sql()

        # Postgres doesn't increase the sequence when specifying the pk when performing inserts
        # We have to do this manually by executing sql
        table_name = model._meta.db_table
        pk_column = model._meta.pk.column
        seq_sql = set_seq_sql.format(table_name=table_name, pk_column=pk_column)

        with connection.cursor() as cursor:
            cursor.execute(seq_sql)


def new_process_pk() -> int:
    return int(Process.objects.exists() and Process.objects.latest("pk").pk) + 1
