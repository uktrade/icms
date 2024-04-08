from django.db.backends.postgresql.base import DatabaseWrapper
from django.db.models import Lookup
from django.db.models.sql.compiler import SQLCompiler


class ILike(Lookup):
    lookup_name = "ilike"

    def as_sql(self, compiler: SQLCompiler, connection: DatabaseWrapper) -> tuple[str, list[str]]:
        """ILIKE lookup to allow better wildcard searches.

        Example usage:
            ImportApplication.objects.filter(reference__ilike="IMA/%3/%3")
        """

        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)

        params = lhs_params + rhs_params

        return f"{lhs} ILIKE {rhs}", params
