from contextlib import contextmanager
from typing import Iterator, List, TypedDict

import sqlparse
from django.db import connections
from pygments import highlight
from pygments.formatters.terminal import TerminalFormatter
from pygments.lexers.sql import MySqlLexer


class Query(TypedDict):
    sql: str
    time: str


@contextmanager
def debug_queries(show_time: bool = True, fancy_print: bool = True) -> Iterator[None]:
    """Debug queries that occur inside with statement block.

    Usage:
        # Everything inside with statement will be printed
        with debug_queries():
            call_db_for_something()
            call_db_for_something_else()

    :param show_time: Shows query times if set to True
    :param fancy_print: Prints sql with formatting and syntax highlighting if set
    :yield None
    """

    # Number of queries to ignore
    ignore = len(connections["default"].queries)

    try:
        yield

    finally:
        _show_queries(ignore, show_time, fancy_print)


def _show_queries(ignore: int, show_time: bool, fancy_print: bool) -> None:
    queries_to_debug: List[Query] = connections["default"].queries[ignore:]

    for query in queries_to_debug:
        sql = query["sql"]

        if show_time:
            print(f"Query (time: {query['time']} seconds)")
        else:
            print("Query:")

        if fancy_print:
            parsed = sqlparse.format(sql, reindent=True, keyword_case="upper")
            highlighted = highlight(parsed, MySqlLexer(), TerminalFormatter())

            print(highlighted)
        else:
            print(sql)

        print("*-" * 40)
