from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from pathlib import Path
import duckdb

from question_engine import understand_question
from gemini_data_agent import generate_sql
from sql_executor import execute_sql
from answer_generator import generate_answer, generate_answer_stream


app = FastAPI(title="Sales Chatbot POC")

DATA_PATH = Path("/tmp/sales_riyadh.parquet")


class ChatRequest(BaseModel):
    question: str
    language: str = "en-US"


def query_database(sql):
    try:
        print("\nSQL:")
        print(sql)

        return duckdb.sql(sql).fetchall()

    except Exception as e:
        print("SQL ERROR:", e)
        return None


def format_number(value):
    if value is None:
        return "0"

    return f"{value:,.2f}"


def build_where(plan, include_dimension=True):

    conditions = []

    dimension = plan.get("dimension")
    filter_column = plan.get("filter_column")
    filter_value = plan.get("filter_value")
    date_filter = plan.get("date_filter")

    if date_filter == "PAST_12_MONTHS":
        date_filter = f"""
            transaction_date >= (
                SELECT MAX(transaction_date)
                FROM read_parquet('{DATA_PATH}')
            ) - INTERVAL '12 months'
        """

    if include_dimension and dimension:
        conditions.append(f"{dimension} IS NOT NULL")

    if filter_column and filter_value:

        safe_value = filter_value.replace("'", "''")

        conditions.append(
            f"LOWER(CAST({filter_column} AS VARCHAR)) "
            f"LIKE LOWER('%{safe_value}%')"
        )

    if date_filter:
        conditions.append(date_filter)

    if not conditions:
        return ""

    return "WHERE " + " AND ".join(conditions)


def answer_question(question, language):
        # Handle greetings before analyzing the sales data
    q = question.strip().lower().strip("!?.,")
    
    greetings = {
    "hi",
    "hello",
    "hey",
    "hii",
    "hiii",
    "good morning",
    "good afternoon",
    "good evening",
    "مرحبا",
    "مرحبًا",
    "السلام عليكم",
    "السلام علیکم"
}

    if q in greetings:
        if language == "ar-SA":
            return "مرحبًا! كيف يمكنني مساعدتك في بيانات المبيعات؟"
        return "Hello! How can I help you with the sales data?"

    # =====================================================
    # GEMINI DATA AGENT
    # =====================================================

    try:
        print("\nUsing Gemini data agent...")

        sql = generate_sql(question)

        print("\nGEMINI SQL:")
        print(sql)

        columns, rows = execute_sql(sql)

        print("\nGEMINI RESULT:")
        print(columns)
        print(rows[:10])

        if rows:
            return generate_answer(
                question,
                columns,
                rows,
                language
            )

    except Exception as e:
        print("\nGEMINI ERROR:", e)
        print("Falling back to existing question engine.")

    # =====================================================
    # EXISTING RULE-BASED ENGINE
    # =====================================================

    plan = understand_question(question)

    print("\nQUESTION PLAN:")
    print(plan)

    data = f"read_parquet('{DATA_PATH}')"

    question_type = plan["question_type"]
    metric = plan["metric"]
    metric_name = plan["metric_name"]

    filter_value = plan.get("product_filter") or plan.get("filter_value")
    date_filter = plan.get("date_filter")

    dimension = plan["dimension"]
    dimension_name = plan["dimension_name"]

    limit = plan["limit"]

    # =====================================================
    # JUICE / CATEGORY BREAKDOWN
    # =====================================================

    if question_type == "breakdown":

        # If user says "juice", give juice-related products
        # and their sales breakdown.
        if plan["filter_column"] == "ibp_product_category":

            sql = f"""
                SELECT
                    product_name,
                    SUM(sales_net_value) AS sales
                FROM {data}
                WHERE LOWER(CAST(ibp_product_category AS VARCHAR))
                    LIKE LOWER('%{plan["filter_value"]}%')
                {"AND " + plan["date_filter"] if plan["date_filter"] else ""}
                GROUP BY product_name
                ORDER BY sales DESC
                LIMIT 20
            """

            result = query_database(sql)

            if result:

                if language == "ar-SA":
                    answer = "تفصيل مبيعات منتجات العصائر:\n"
                else:
                    answer = "Juice sales breakdown:\n"

                total = 0

                for name, sales in result:
                    total += sales or 0

                    answer += (
                        f"{name}: "
                        f"{format_number(sales)} SAR\n"
                    )

                answer += (
                    f"\nTotal: {format_number(total)} SAR"
                )

                return answer

        # Normal breakdown by dimension
        if dimension:

            where_clause = build_where(plan)

            sql = f"""
                SELECT
                    {dimension},
                    SUM({metric}) AS total_value
                FROM {data}
                {where_clause}
                GROUP BY {dimension}
                ORDER BY total_value DESC
                LIMIT 20
            """

            result = query_database(sql)

            if result:

                if language == "ar-SA":
                    answer = (
                        f"تفصيل {metric_name} حسب "
                        f"{dimension_name}:\n"
                    )
                else:
                    answer = (
                        f"{metric_name.title()} breakdown by "
                        f"{dimension_name}:\n"
                    )

                for name, value in result:
                    answer += (
                        f"{name}: "
                        f"{format_number(value)}\n"
                    )

                return answer

    # =====================================================
    # RETURN RATE
    # =====================================================

    if question_type == "return_rate":

        if not dimension:
            dimension = "product_name"
            dimension_name = "product"

        where_clause = build_where(
            {
                **plan,
                "dimension": dimension
            }
        )

        sql = f"""
            SELECT
                {dimension},
                SUM(
                    sales_good_return_volume
                    + sales_bad_return_volume
                ) AS returned_volume,
                SUM(sales_gross_volume) AS gross_volume
            FROM {data}
            {where_clause}
            {"AND" if where_clause else "WHERE"}
                sales_gross_volume > 0
            GROUP BY {dimension}
            ORDER BY
                returned_volume / NULLIF(gross_volume, 0) DESC
            LIMIT {limit}
        """

        result = query_database(sql)

        if result:

            if language == "ar-SA":
                answer = f"أعلى {limit} حسب نسبة المرتجعات:\n"
            else:
                answer = f"Top {limit} by return rate:\n"

            for name, returned, gross in result:

                rate = 0

                if gross:
                    rate = (returned / gross) * 100

                answer += (
                    f"{name}: "
                    f"{rate:.2f}% "
                    f"({format_number(returned)} L returned)\n"
                )

            return answer

        # =====================================================
    # TREND
    # =====================================================

    if question_type == "trend":

        filter_value = plan.get("product_filter") or plan.get("filter_value")
        date_filter = plan.get("date_filter")

        if date_filter == "PAST_12_MONTHS":
            date_filter = f"""
                transaction_date >= (
                    SELECT MAX(transaction_date)
                    FROM {data}
                ) - INTERVAL '12 months'
            """

        if filter_value:

            safe_value = filter_value.replace("'", "''")

            conditions = [
                f"LOWER(CAST(product_name AS VARCHAR)) "
                f"LIKE LOWER('%{safe_value}%')"
            ]

            if date_filter:
                conditions.append(date_filter)

            where_clause = " AND ".join(conditions)

            sql = f"""
                SELECT
                    DATE_TRUNC('month', transaction_date) AS month,
                    SUM({metric}) AS total_value
                FROM {data}
                WHERE {where_clause}
                GROUP BY month
                ORDER BY month
            """

            result = query_database(sql)

            if result:

                if language == "ar-SA":
                    answer = (
                        f"الاتجاه الشهري لمبيعات {filter_value}:\n"
                    )
                else:
                    answer = (
                        f"Monthly sales trend for "
                        f"{filter_value}:\n"
                    )

                for month, value in result:
                    answer += (
                        f"{month.strftime('%Y-%m')}: "
                        f"{format_number(value)}\n"
                    )

                return answer

        # Overall monthly trend
        sql = f"""
            SELECT
                DATE_TRUNC('month', transaction_date) AS month,
                SUM({metric}) AS total_value
            FROM {data}
            {"WHERE " + date_filter if date_filter else ""}
            GROUP BY month
            ORDER BY month
        """

        result = query_database(sql)

        if result:

            if language == "ar-SA":
                answer = "الاتجاه الشهري للمبيعات:\n"
            else:
                answer = "Monthly sales trend:\n"

            for month, value in result:
                answer += (
                    f"{month.strftime('%Y-%m')}: "
                    f"{format_number(value)}\n"
                )

            return answer

    # =====================================================
    # TOP / BOTTOM
    # =====================================================

    if question_type in ["top", "bottom"]:

        if not dimension:
            dimension = "product_name"
            dimension_name = "product"

        order = (
            "ASC"
            if question_type == "bottom"
            else "DESC"
        )

        where_clause = build_where(
            {
                **plan,
                "dimension": dimension
            }
        )

        sql = f"""
            SELECT
                {dimension},
                SUM({metric}) AS total_value
            FROM {data}
            {where_clause}
            GROUP BY {dimension}
            ORDER BY total_value {order}
            LIMIT {limit}
        """

        result = query_database(sql)

        if result:

            if question_type == "bottom":

                if language == "ar-SA":
                    answer = (
                        f"أقل {limit} {dimension_name} "
                        f"حسب {metric_name}:\n"
                    )
                else:
                    answer = (
                        f"Bottom {limit} {dimension_name} "
                        f"by {metric_name}:\n"
                    )

            else:

                if language == "ar-SA":
                    answer = (
                        f"أفضل {limit} {dimension_name} "
                        f"حسب {metric_name}:\n"
                    )
                else:
                    answer = (
                        f"Top {limit} {dimension_name} "
                        f"by {metric_name}:\n"
                    )

            for name, value in result:

                answer += (
                    f"{name}: "
                    f"{format_number(value)}\n"
                )

            return answer

    # =====================================================
    # COUNT
    # =====================================================

    if question_type == "count":

        if "customer" in question.lower():

            sql = f"""
                SELECT COUNT(DISTINCT customer_name)
                FROM {data}
            """

            result = query_database(sql)

            if result:

                value = result[0][0]

                if language == "ar-SA":
                    return f"عدد العملاء هو {value:,}."

                return f"There are {value:,} unique customers."

        sql = f"""
            SELECT COUNT(DISTINCT product_name)
            FROM {data}
        """

        result = query_database(sql)

        if result:

            value = result[0][0]

            if language == "ar-SA":
                return f"عدد المنتجات هو {value:,}."

            return f"There are {value:,} unique products."

    # =====================================================
    # AVERAGE
    # =====================================================

    if question_type == "average":

        where_clause = build_where(plan)

        sql = f"""
            SELECT AVG({metric})
            FROM {data}
            {where_clause}
        """

        result = query_database(sql)

        if result and result[0][0] is not None:

            value = result[0][0]

            if language == "ar-SA":
                return (
                    f"متوسط {metric_name} هو "
                    f"{format_number(value)}."
                )

            return (
                f"Average {metric_name} is "
                f"{format_number(value)}."
            )

    # =====================================================
    # TOTAL
    # =====================================================

    if question_type == "total":

        where_clause = build_where(plan, include_dimension=False)

        sql = f"""
            SELECT SUM({metric})
            FROM {data}
            {where_clause}
        """

        result = query_database(sql)

        if result and result[0][0] is not None:

            value = result[0][0]

            if language == "ar-SA":
                return (
                    f"إجمالي {metric_name} هو "
                    f"{format_number(value)}."
                )

            return (
                f"Total {metric_name} is "
                f"{format_number(value)}."
            )

    # =====================================================
    # SPECIFIC PRODUCT / CATEGORY / CUSTOMER
    # =====================================================

    if dimension:

        filter_value = plan.get("filter_value")

        if filter_value:

            safe_value = filter_value.replace("'", "''")

            date_condition = ""

            if plan.get("date_filter"):
                date_condition = (
                    f"AND {plan['date_filter']}"
                )

            sql = f"""
                SELECT
                    {dimension},
                    SUM({metric}) AS total_value
                FROM {data}
                WHERE LOWER(CAST({dimension} AS VARCHAR))
                    LIKE LOWER('%{safe_value}%')
                    {date_condition}
                GROUP BY {dimension}
                ORDER BY total_value DESC
                LIMIT 5
            """

            result = query_database(sql)

            if result:

                if language == "ar-SA":
                    answer = (
                        f"نتائج {dimension_name} "
                        f"حسب {metric_name}:\n"
                    )
                else:
                    answer = (
                        f"{dimension_name.title()} results "
                        f"by {metric_name}:\n"
                    )

                for name, value in result:

                    answer += (
                        f"{name}: "
                        f"{format_number(value)}\n"
                    )

                return answer

    # =====================================================
    # FALLBACK
    # =====================================================

    if language == "ar-SA":
        return (
            "لم أتمكن من تحديد السؤال بدقة. "
            "يمكنني تحليل المبيعات والمنتجات والعملاء "
            "والفئات والقنوات والمناطق والمرتجعات والهدر."
        )

    return (
        "I could not determine the exact analysis requested. "
        "I can analyze sales, products, customers, categories, "
        "channels, regions, returns and wasted volume."
    )


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.post("/chat")
def chat(request: ChatRequest):

    answer = answer_question(
        request.question,
        request.language
    )

    return {
        "question": request.question,
        "language": request.language,
        "answer": answer
    }

@app.post("/chat/stream")
def chat_stream(request: ChatRequest):

    print("LANGUAGE RECEIVED:", request.language)

    def generate():

        try:
            
            sql = generate_sql(request.question)
            

            print("\nSTREAM SQL:")
            print(sql)

            columns, rows = execute_sql(sql)

            print("\nSTREAM RESULT:")
            print(columns)
            print(rows[:10])
            

            for chunk in generate_answer_stream(
                request.question,
                columns,
                rows,
                request.language
            ):
                yield chunk

        except Exception as e:
            print("\nSTREAM ERROR:", e)
            yield "Sorry, I could not process your request."

    return StreamingResponse(
        generate(),
        media_type="text/plain; charset=utf-8"
    )