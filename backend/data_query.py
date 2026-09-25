import duckdb
from pathlib import Path


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "sales_riyadh.parquet"


def run_query(sql):
    """
    Execute a SQL query against the sales Parquet dataset.
    """
    try:
        result = duckdb.sql(sql).fetchall()
        columns = [col[0] for col in duckdb.sql(sql).description]
        return columns, result

    except Exception as e:
        return None, str(e)


def get_total_sales():
    sql = f"""
        SELECT SUM(sales_net_value)
        FROM read_parquet('{DATA_PATH}')
    """

    result = duckdb.sql(sql).fetchone()[0]
    return result or 0


def get_top_products(limit=5):
    sql = f"""
        SELECT
            product_name,
            SUM(sales_net_value) AS total_sales
        FROM read_parquet('{DATA_PATH}')
        WHERE product_name IS NOT NULL
        GROUP BY product_name
        ORDER BY total_sales DESC
        LIMIT {limit}
    """

    return duckdb.sql(sql).fetchall()


def get_product_sales(product_name):
    safe_name = product_name.replace("'", "''")

    sql = f"""
        SELECT
            product_name,
            SUM(sales_net_value) AS total_sales
        FROM read_parquet('{DATA_PATH}')
        WHERE LOWER(product_name) = LOWER('{safe_name}')
        GROUP BY product_name
    """

    return duckdb.sql(sql).fetchall()


def get_data_summary():
    """
    Return basic information about the dataset.
    """
    sql = f"""
        SELECT
            COUNT(*) AS row_count,
            COUNT(DISTINCT product_name) AS product_count,
            COUNT(DISTINCT customer_name) AS customer_count,
            MIN(transaction_date) AS first_date,
            MAX(transaction_date) AS last_date,
            SUM(sales_net_value) AS total_net_sales
        FROM read_parquet('{DATA_PATH}')
    """

    return duckdb.sql(sql).fetchone()