import duckdb


def execute_sql(sql: str):
    sql = sql.strip()

    if not sql.lower().startswith(("select", "with")):
        raise ValueError("Only SELECT or WITH queries are allowed.")

    forbidden = [
        "insert ",
        "update ",
        "delete ",
        "drop ",
        "alter ",
        "create ",
        "copy ",
        "install ",
        "load ",
        "attach ",
    ]

    sql_lower = sql.lower()

    for word in forbidden:
        if word in sql_lower:
            raise ValueError("Unsafe SQL query detected.")

    result = duckdb.sql(sql)

    columns = [column[0] for column in result.description]
    rows = result.fetchall()

    return columns, rows
