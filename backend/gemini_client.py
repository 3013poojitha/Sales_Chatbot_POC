import os
import requests
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    try:
        import streamlit as st
        API_KEY = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        API_KEY = None

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found")


def ask_gemini(prompt: str) -> str:
    """
    Normal Gemini request.
    Used for SQL generation and other non-streaming tasks.
    """

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-3.8-flash:generateContent"
        f"?key={API_KEY}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    response = requests.post(
        url,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    return data["candidates"][0]["content"]["parts"][0]["text"]


def stream_gemini(prompt: str):
    """
    Streaming Gemini request.

    Yields pieces of the response as Gemini generates them.
    """

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-3.8-flash:streamGenerateContent"
        f"?alt=sse&key={API_KEY}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    with requests.post(
        url,
        json=payload,
        stream=True,
        timeout=120
    ) as response:

        response.raise_for_status()

        for line in response.iter_lines(decode_unicode=True):

            if not line:
                continue

            if line.startswith("data:"):
                data = line[5:].strip()

                if data == "[DONE]":
                    break

                try:
                    chunk = json.loads(data)

                    candidates = chunk.get("candidates", [])

                    if not candidates:
                        continue

                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])

                    for part in parts:
                        text = part.get("text")

                        if text:
                            yield text

                except json.JSONDecodeError:
                    continue


def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
    """
    Convert recorded speech audio into text using Gemini.
    """

    client = genai.Client(api_key=API_KEY)

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=[
            types.Part.from_bytes(
                data=audio_bytes,
                mime_type=mime_type
            ),
            """
            Transcribe the speech in this audio.

            Important:
            - Detect whether the speaker is using English or Arabic.
            - Return ONLY the spoken words as text.
            - Do not translate the speech.
            - Do not add explanations.
            - Do not answer the question.
            """
        ]
    )

    return response.text.strip()