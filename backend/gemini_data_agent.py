import json
from gemini_client import ask_gemini


SCHEMA = """
Dataset: sales_riyadh.parquet
Rows: approximately 36.98 million

Important columns:

Sales measures:
- sales_net_value
- sales_raw_value
- sales_gross_value
- sales_net_volume
- sales_gross_volume
- sales_good_return_value
- sales_good_return_volume
- sales_bad_return_value
- sales_bad_return_volume

Date:
- transaction_date

Product:
- product_code
- product_name
- product_group
- ibp_product_name
- ibp_product_category
- ibp_product_family
- ibp_product_group
- ibp_product_subfamily
- ibp_product_section

Customer:
- customer_code
- customer_name
- customer_tier
- ibp_customer_id
- ibp_customer_name
- ibp_customer_channel
- ibp_customer_segment
- ibp_customer_region
- ibp_customer_subarea
- ibp_customer_salesarea
- ibp_is_key_account

Route:
- route_code
- route_name
- route_type
- route_subarea
- route_area

Distribution center:
- dc_code
- dc_name

Other:
- life_type
- is_imp_category
- weight_kg
"""

DATA_PATH = r"C:\Users\pooji\Downloads\Sales_Chatbot_POC\data\sales_riyadh.parquet"


def generate_sql(question: str) -> str:

    prompt = f"""
You are a SQL analyst for a sales chatbot.

The user asks:
{question}

You must convert the user's question into a DuckDB SQL query.

DATABASE:
The data is stored in this Parquet file:

{DATA_PATH}

SCHEMA:
{SCHEMA}

Rules:

1. Generate ONLY a SELECT or WITH SQL query.
2. Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, COPY, INSTALL, LOAD, or ATTACH.
3. Always read the data using:
   read_parquet('{DATA_PATH}')
4. Use sales_net_value as the default sales metric unless the user asks for another sales measure.
5. Use transaction_date for date filtering and time-based analysis.
6. Use LOWER() when comparing text values so matching is case-insensitive.
7. For rankings such as top products, use ORDER BY and LIMIT.
8. For totals, use SUM().
9. For counts, use COUNT().
10. For averages, use AVG().
11. Return only the SQL query.
12. Do not use markdown code fences.

Generate the SQL now.
"""

    sql = ask_gemini(prompt)

    return sql.strip()