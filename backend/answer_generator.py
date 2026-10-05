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
4. Present tabular results as a clean Markdown table.
5. Do not use bold text, asterisks, bullet points, or numbered-list formatting.
6. Use clear table headers appropriate to the response language.
7. Format monetary values with "SAR", commas, and 2 decimal places. Never use "$".
8. Keep the answer neat and easy to read.
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

    answer = generate_answer(
        question,
        columns,
        rows,
        language
    )

    # Send the answer in small pieces so the UI
    # still appears to respond progressively.
    chunk_size = 25

    for i in range(0, len(answer), chunk_size):
        yield answer[i:i + chunk_size]