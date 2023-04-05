from django.db.models import Lookup


class ILike(Lookup):
    lookup_name = "ilike"

    def as_sql(self, compiler, connection):
        """Generates the SQL fragment for the expression.

        Returns a tuple (sql, params), where sql is the SQL string, and params
        is the list or tuple of query parameters. The compiler is an SQLCompiler
        object, which has a compile() method that can be used to compile other
        expressions. The connection is the connection used to execute the query.

        Example usage:
            ImportApplication.objects.filter(reference__ilike="IMA/%3/%3")
        """

        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)

        params = lhs_params + rhs_params

        return f"{lhs} ILIKE {rhs}", params
