from gemini_client import ask_gemini, stream_gemini


def build_answer_prompt(question, columns, rows, language="en-US"):

    if language == "ar-SA":
        response_language = "Arabic"
    else:
        response_language = "English"

    result_text = ""

    for row in rows:
        result_text += str(row) + "\n"

    prompt = f"""
You are a sales data chatbot.

User question:
{question}

Database result:
Columns: {columns}

Rows:
{result_text}

Answer the user's question using ONLY the database result provided above.

Response language:
{response_language}

Rules:
1. Never invent numbers or facts.
2. Do not mention SQL, Python, DuckDB, Gemini, or the database.
3. Give a clear and concise business-friendly answer.
4. If there are multiple results, use a numbered list or bullet list.
5. Format monetary values with "SAR", commas, and 2 decimal places. Never use "$".
"""

    return prompt


def generate_answer(question, columns, rows, language="en-US"):

    prompt = build_answer_prompt(
        question,
        columns,
        rows,
        language
    )

    return ask_gemini(prompt)


def generate_answer_stream(question, columns, rows, language="en-US"):

    prompt = build_answer_prompt(
        question,
        columns,
        rows,
        language
    )

    return stream_gemini(prompt)