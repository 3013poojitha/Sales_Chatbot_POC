import duckdb

con = duckdb.connect()

result = con.execute("""
    SELECT COUNT(*) AS rows
    FROM '../data/sales_riyadh.parquet'
""").fetchall()

print(result)