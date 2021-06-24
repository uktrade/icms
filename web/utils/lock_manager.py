from typing import Type

from django.db import connection, models, transaction


class LockManager:
    """Manages locking database tables in a deadlock-free way."""

    def __init__(self):
        # have we been activated
        self.activated = False

        # which tables are locked
        self.locked_tables: set[str] = set()

    def lock_tables(self, tables: list[Type[models.Model]]) -> None:
        if not tables:
            raise RuntimeError("no tables given")

        if transaction.get_autocommit():
            raise RuntimeError(
                "lock_tables cannot be called without being inside a database transaction"
            )

        if self.activated:
            raise RuntimeError("lock_tables has already been called")

        self.activated = True

        # sorting the tables by name is a way to achieve a deterministic locking
        # order that will avoid deadlocks. google "lock hierarchy" if you
        # don't understand what this means.
        sorted_table_names = sorted(table._meta.db_table for table in tables)

        cursor = connection.cursor()

        for table in sorted_table_names:
            cursor.execute(f"LOCK TABLE {table}")
            self.locked_tables.add(table)

    def is_table_locked(self, table: Type[models.Model]) -> bool:
        """Check if the table is locked."""

        return table._meta.db_table in self.locked_tables

    def ensure_tables_are_locked(self, tables: list[Type[models.Model]]) -> None:
        """If some deeply nested code wants to:

          a) ensure some tables are locked

          b) not have to bother every caller having to lock them themselves

          c) still allow flexibility for some callers to lock other tables as
          well for more complex cases

        it can use this function. This function will:

          * If nobody has locked any tables yet: lock the given tables
          * Otherwise check the given tables are a subset of the already-locked
            tables. If they are not, an error will be raised.
        """

        if self.activated:
            # lock_tables has already been called; verify all needed tables were included

            not_locked = {table._meta.db_table for table in tables} - self.locked_tables

            if not_locked:
                raise RuntimeError(f"cannot lock extra tables: {not_locked}")
        else:
            self.lock_tables(tables)
