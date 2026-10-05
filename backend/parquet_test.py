import duckdb

PARQUET_FILE = "../data/sales_riyadh.parquet"

con = duckdb.connect()

# Total number of rows
total_rows = con.execute(f"""
    SELECT COUNT(*)
    FROM read_parquet('{PARQUET_FILE}')
""").fetchone()[0]

print("Total rows:", total_rows)


# Total sales
total_sales = con.execute(f"""
    SELECT SUM(sales_net_value)
    FROM read_parquet('{PARQUET_FILE}')
""").fetchone()[0]

print("Total sales:", total_sales)


# Top 5 products by sales
top_products = con.execute(f"""
    SELECT
        product_name,
        SUM(sales_net_value) AS total_sales
    FROM read_parquet('{PARQUET_FILE}')
    GROUP BY product_name
    ORDER BY total_sales DESC
    LIMIT 5
""").fetchdf()

print("\nTop 5 products by sales:")
print(top_products.to_string(index=False))