import streamlit as st
from main import answer_question


# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="Sales Chatbot",
    page_icon="💬",
    layout="centered"
)


# =========================================================
# HEADER
# =========================================================

st.title("💬 Sales Chatbot")
st.caption("Ask questions about sales, products, customers, categories, channels, regions, returns and waste.")


# =========================================================
# LANGUAGE
# =========================================================

language = st.selectbox(
    "Answer language",
    options=["English", "Arabic"],
    index=0
)

language_code = "en-US" if language == "English" else "ar-SA"


# =========================================================
# CHAT HISTORY
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# =========================================================
# CHAT INPUT
# =========================================================

question = st.chat_input(
    "Ask a question about the sales data..."
)


# =========================================================
# PROCESS QUESTION
# =========================================================

if question:

    # Show user question
    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    with st.chat_message("user"):
        st.markdown(question)

    # Generate answer
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

    # Save answer
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer
        }
    )