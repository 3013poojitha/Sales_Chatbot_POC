import re


# =========================================================
# COLUMN ALIASES
# =========================================================

METRICS = {
    "sales": "sales_net_value",
    "net sales": "sales_net_value",
    "revenue": "sales_net_value",
    "sales value": "sales_net_value",

    "gross sales": "sales_gross_value",
    "gross revenue": "sales_gross_value",

    "raw sales": "sales_raw_value",

    "volume": "sales_net_volume",
    "net volume": "sales_net_volume",
    "quantity": "sales_net_volume",
    "units": "sales_net_volume",

    "waste": "sales_bad_return_volume",
    "wasted volume": "sales_bad_return_volume",
    "waste volume": "sales_bad_return_volume",
    "bad return": "sales_bad_return_volume",
    "bad returns": "sales_bad_return_volume",

    "good return": "sales_good_return_volume",
    "good returns": "sales_good_return_volume",

    "return volume": (
        "sales_good_return_volume + sales_bad_return_volume"
    ),

    "weight": "weight_kg",
    "kg": "weight_kg",
}


DIMENSIONS = {
    "product": ("product_name", "product"),
    "products": ("product_name", "product"),

    "category": ("ibp_product_category", "product category"),
    "product category": ("ibp_product_category", "product category"),

    "product group": ("product_group", "product group"),
    "group": ("product_group", "product group"),

    "family": ("ibp_product_family", "product family"),
    "product family": ("ibp_product_family", "product family"),

    "customer": ("customer_name", "customer"),
    "customers": ("customer_name", "customer"),

    "customer tier": ("customer_tier", "customer tier"),

    "channel": ("ibp_customer_channel", "channel"),
    "customer channel": ("ibp_customer_channel", "customer channel"),

    "segment": ("ibp_customer_segment", "segment"),
    "customer segment": ("ibp_customer_segment", "customer segment"),

    "region": ("ibp_customer_region", "region"),

    "subarea": ("ibp_customer_subarea", "subarea"),

    "sales area": ("ibp_customer_salesarea", "sales area"),

    "route": ("route_name", "route"),
    "route type": ("route_type", "route type"),
    "route area": ("route_area", "route area"),
}


# =========================================================
# QUESTION UNDERSTANDING
# =========================================================

def clean_question(question):
    return re.sub(r"\s+", " ", question.lower().strip())


def detect_metric(question):
    q = clean_question(question)

    # Check longer phrases first
    phrases = sorted(METRICS.keys(), key=len, reverse=True)

    for phrase in phrases:
        if phrase in q:
            return METRICS[phrase], phrase

    # Default business metric
    return "sales_net_value", "sales"


def detect_dimension(question):
    q = clean_question(question)

    phrases = sorted(DIMENSIONS.keys(), key=len, reverse=True)

    for phrase in phrases:
        if phrase in q:
            column, name = DIMENSIONS[phrase]
            return column, name

    # Most product questions are naturally product-level
    if "juice" in q or "juices" in q:
        return "ibp_product_category", "product category"

    return None, None


# =========================================================
# NUMBER / RANK
# =========================================================

def detect_number(question):
    match = re.search(r"\b(\d+)\b", question)

    if match:
        return int(match.group(1))

    return 5


def is_top_question(question):
    q = clean_question(question)

    return any(
        phrase in q
        for phrase in [
            "top ",
            "highest",
            "best",
            "largest",
            "most",
        ]
    )


def is_bottom_question(question):
    q = clean_question(question)

    return any(
        phrase in q
        for phrase in [
            "bottom ",
            "lowest",
            "worst",
            "smallest",
            "least",
            "not good",
            "no good sales",
        ]
    )


# =========================================================
# DATE UNDERSTANDING
# =========================================================

def detect_date_filter(question):
    q = clean_question(question)

    # 2025-2026
    match = re.search(
        r"(20\d{2})\s*[-–—]\s*(20\d{2})",
        q
    )

    if match:
        start_year = int(match.group(1))
        end_year = int(match.group(2))

        return (
            f"transaction_date >= DATE '{start_year}-01-01' "
            f"AND transaction_date < DATE '{end_year + 1}-01-01'"
        )

    # From 2025 to 2026
    match = re.search(
        r"from\s+(20\d{2})\s+to\s+(20\d{2})",
        q
    )

    if match:
        start_year = int(match.group(1))
        end_year = int(match.group(2))

        return (
            f"transaction_date >= DATE '{start_year}-01-01' "
            f"AND transaction_date < DATE '{end_year + 1}-01-01'"
        )

    # Past / last 12 months
    if (
        "past 12 months" in q
        or "last 12 months" in q
    ):
        return "PAST_12_MONTHS"

    # Single year
    years = re.findall(r"\b(20\d{2})\b", q)

    if len(years) == 1:
        year = int(years[0])

        return (
            f"transaction_date >= DATE '{year}-01-01' "
            f"AND transaction_date < DATE '{year + 1}-01-01'"
        )

    return None

# =========================================================
# SPECIAL BUSINESS TERMS
# =========================================================

def detect_category_filter(question):
    q = clean_question(question)

    # Juice / juices
    if re.search(r"\bjuices?\b", q):
        return (
            "ibp_product_category",
            "Juice"
        )

    return None


def detect_product_filter(question):
    """
    Detect a specific product name from common
    natural-language question patterns.
    """

    q = clean_question(question)

    # Product mentioned after "for"
    match = re.search(
        r"\bfor\s+(.+?)(?=\s+(?:over|during|from|in)\b|$)",
        q
    )

    if match:
        value = match.group(1).strip()

        # Remove common trailing words
        value = re.sub(
            r"\b(the|product|sales|trend)\b$",
            "",
            value
        ).strip()

        if value:
            return value

    # Product code
    code_match = re.search(
        r"\b\d{6,}\b",
        q
    )

    if code_match:
        return code_match.group(0)

    return None


# =========================================================
# QUESTION TYPE
# =========================================================

def detect_question_type(question):
    q = clean_question(question)

    if (
        "return rate" in q
        or "return rates" in q
        or "return percentage" in q
        or "return rate percentage" in q
    ):
        return "return_rate"

    if (
        "trend" in q
        or "over the past" in q
        or "over time" in q
        or "month by month" in q
        or "monthly" in q
    ):
        return "trend"

    if (
        "breakdown" in q
        or "break down" in q
        or "break-up" in q
        or "break up" in q
        or "by category" in q
        or "by product" in q
        or "by customer" in q
        or "by region" in q
        or "by channel" in q
    ):
        return "breakdown"

    if is_top_question(q):
        return "top"

    if is_bottom_question(q):
        return "bottom"

    if (
        "how many" in q
        or "number of" in q
        or "count of" in q
        or "count" in q
    ):
        return "count"

    if (
        "average" in q
        or "avg" in q
        or "mean" in q
    ):
        return "average"

    if (
        "total" in q
        or "sum" in q
        or "overall" in q
        or "how much" in q
    ):
        return "total"

    return "specific"


# =========================================================
# BUILD A QUERY PLAN
# =========================================================

def understand_question(question):
    """
    Convert natural-language business question into
    a structured plan.

    This plan is then used by the SQL layer.
    """

    metric, metric_name = detect_metric(question)

    dimension, dimension_name = detect_dimension(question)

    question_type = detect_question_type(question)

    number = detect_number(question)

    date_filter = detect_date_filter(question)

    category_filter = detect_category_filter(question)

    product_filter = detect_product_filter(question)

    # Juice is a category filter
    if category_filter:
        filter_column, filter_value = category_filter
    else:
        filter_column = None
        filter_value = None

    return {
        "question": question,
        "question_type": question_type,

        "metric": metric,
        "metric_name": metric_name,

        "dimension": dimension,
        "dimension_name": dimension_name,

        "limit": number,

        "date_filter": date_filter,

        "filter_column": filter_column,
        "filter_value": filter_value,

        "product_filter": product_filter,
    }