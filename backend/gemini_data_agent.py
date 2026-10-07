import json
import os
import gdown
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

DATA_PATH = "/tmp/sales_riyadh.parquet" if os.name != "nt" else str(
    __import__("pathlib").Path(__file__).resolve().parent.parent / "data" / "sales_riyadh.parquet"
)

GOOGLE_DRIVE_FILE_ID = "1XAoEioXbXXeWbbbNrGDsAMpJCxswBuzI"

if not os.path.exists(DATA_PATH):
    print("Downloading sales data from Google Drive...")
    gdown.download(
        f"https://drive.google.com/uc?id={GOOGLE_DRIVE_FILE_ID}",
        DATA_PATH,
        quiet=False
    )
    print("Sales data download completed.")


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
4. Metric rules:
   - "sales", "sales value", "revenue", or "amount" → SUM(sales_net_value)
   - "raw sales" → SUM(sales_raw_value)
   - "gross sales" → SUM(sales_gross_value)
   - "sales volume" or "net volume" → SUM(sales_net_volume)
   - "gross volume" → SUM(sales_gross_volume)
   - "good returns" → SUM(sales_good_return_value)
   - "good return volume" → SUM(sales_good_return_volume)
   - "bad returns", "waste", or "wasted value" → SUM(sales_bad_return_value)
   - "bad return volume", "wasted volume", or "waste volume" → SUM(sales_bad_return_volume)

5. Never substitute one metric for another.
6. Use transaction_date for date filtering and time-based analysis.
7. Use LOWER() when comparing text values so matching is case-insensitive.
8. For rankings:
   - top products → GROUP BY product_name
   - top customers → GROUP BY customer_name
   - top routes → GROUP BY route_name
   - top distribution centers → GROUP BY dc_name
   - top categories → GROUP BY the requested category field
   Always ORDER BY the requested metric DESC and use LIMIT when requested.
9. For totals, use SUM() of the requested metric.
10. For counts, use COUNT().
11. Return only the SQL query.
12. Do not use markdown code fences.

Generate the SQL now.
"""

    sql = ask_gemini(prompt)

    return sql.strip()