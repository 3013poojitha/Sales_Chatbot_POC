import streamlit as st
from main import answer_question
from gemini_client import transcribe_audio


# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="Sales Chatbot",
    page_icon="💬",
    layout="centered"
)
# =========================================================
# CUSTOM THEME
# =========================================================

st.markdown(
    """
    <style>

    /* Main page */
    .stApp {
        background-color: #FFF8EE;
        color: #4A2C1A;
    }

    /* Main text */
    .stApp,
    .stApp p,
    .stApp span,
    .stApp label,
    .stMarkdown,
    .stCaption {
        color: #4A2C1A !important;
    }

    /* Header */
    h1 {
        color: #C96F2D !important;
        font-weight: 700;
    }

    /* Chat messages */
    [data-testid="stChatMessage"] {
        background-color: #FFFDF8;
        border: 1px solid #F0D2B3;
        border-radius: 16px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }

    /* Chat answer/question text */
    [data-testid="stChatMessage"] p {
        color: #3F2A1D !important;
        font-size: 16px;
    }

    /* Text input */
    div[data-testid="stTextInput"] input {
        background-color: #FFFDF8 !important;
        color: #3F2A1D !important;
        border: 1px solid #E7B789 !important;
        border-radius: 14px !important;
        height: 48px !important;
        font-size: 15px !important;
    }

    div[data-testid="stTextInput"] input::placeholder {
        color: #8A6A55 !important;
        opacity: 1 !important;
    }

    /* Language selector */
    div[data-baseweb="select"] > div {
        background-color: #FFFDF8 !important;
        color: #3F2A1D !important;
        border: 1px solid #E7B789 !important;
        border-radius: 14px !important;
        min-height: 48px !important;
    }

    div[data-baseweb="select"] span {
        color: #3F2A1D !important;
    }

    /* Microphone recorder */
    div[data-testid="stAudioInput"] {
        background-color: #FFFDF8 !important;
        border: 1px solid #E7B789 !important;
        border-radius: 14px !important;
        height: 48px !important;
        min-height: 48px !important;
        padding: 0 !important;
        overflow: hidden;
    }

    div[data-testid="stAudioInput"] button {
        height: 48px !important;
        width: 100% !important;
        border-radius: 14px !important;
    }

    /* Send button */
    .stButton > button {
        background-color: #F4A261 !important;
        color: white !important;
        border: none !important;
        border-radius: 14px !important;
        height: 48px !important;
        font-size: 20px !important;
        font-weight: 600;
    }

    .stButton > button:hover {
        background-color: #D97706 !important;
        color: white !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================
# HEADER
# =========================================================

st.title("💬 Sales Chatbot")
st.caption("Ask questions about sales, products, customers, categories, channels, regions, returns and waste.")


# =========================================================
# LANGUAGE
# =========================================================

# Language will be selected in the chat composer

# =========================================================
# CHAT HISTORY
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# =========================================================
# CHAT COMPOSER
# =========================================================

st.markdown(
    """
    <div class="composer-title">
        Ask your sales question
    </div>
    """,
    unsafe_allow_html=True
)

col1, col2, col3, col4 = st.columns([6, 1, 1.5, 0.8])

if "input_key" not in st.session_state:
    st.session_state.input_key = 0

with col1:
    question = st.text_input(
        "Question",
        placeholder="Type your question here...",
        label_visibility="collapsed",
        key=f"question_input_{st.session_state.input_key}"
    )

with col2:
    audio_value = st.audio_input(
        "🎤",
        label_visibility="collapsed"
    )

with col3:
    language = st.selectbox(
        "Language",
        options=["English", "Arabic"],
        index=0,
        label_visibility="collapsed"
    )

with col4:
    send_clicked = st.button(
        "➤",
        use_container_width=True
    )

language_code = "en-US" if language == "English" else "ar-SA"


# =========================================================
# PROCESS TYPED QUESTION
# =========================================================

if send_clicked and question.strip():

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):

        with st.spinner("Analyzing the sales data..."):

            try:

                answer = answer_question(
                    question,
                    language_code
                )

                st.markdown(answer)

            except Exception as e:

                answer = (
                    "Sorry, I could not process your question."
                )

                st.error(answer)

                print("STREAMLIT ERROR:", e)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer
                }
            )

            st.session_state.input_key += 1

            st.rerun()



# =========================================================
# PROCESS VOICE QUESTION
# =========================================================

if audio_value:

    with st.spinner("Transcribing your voice..."):

        try:

            audio_bytes = audio_value.getvalue()

            transcribed_text = transcribe_audio(
                audio_bytes,
                audio_value.type
            )

            if transcribed_text.strip():

                st.session_state.messages.append(
                    {
                        "role": "user",
                        "content": transcribed_text
                    }
                )

                with st.chat_message("user"):
                    st.markdown(transcribed_text)

                with st.chat_message("assistant"):

                    with st.spinner("Analyzing the sales data..."):

                        answer = answer_question(
                            transcribed_text,
                            language_code
                        )

                        st.markdown(answer)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer
                    }
                )

                st.rerun()

        except Exception as e:

            st.error(
                "Sorry, I could not understand the audio."
            )

            print("VOICE ERROR:", e)