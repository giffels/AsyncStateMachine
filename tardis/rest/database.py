from ..plugins.sqliteregistry import SqliteRegistry


def get_sql_registry():
    sql_registry = SqliteRegistry()
    return lambda: sql_registry
