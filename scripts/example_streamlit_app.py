"""Simple streamlit frontend"""

import os
import sys
from dotenv import load_dotenv
from typing import List, Final, Generator
from datetime import datetime
import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ragxiv.database import (
    open_db_connection,
    PostgresParams,
    SemanticSearch,
)
from ragxiv.retrieval import retrieve_similar_documents
from ragxiv.llm import llm_chat_completion, GroqParams, build_rag_prompt

from groq import Groq


load_dotenv("./.env")

st.set_page_config(
    page_icon="💬",
    layout="wide",
    page_title="ragXiv - Retrieval-Augmented Genearation with arXiv knowledge base",
)

# Default embedding parameters
EMBEDDING_MODEL_NAME: Final = "multi-qa-mpnet-base-dot-v1"

TABLE_EMBEDDING_ARTICLE = f"embedding_article_{EMBEDDING_MODEL_NAME}".replace("-", "_")
TABLE_EMBEDDING_ABSTRACT = f"embedding_abstract_{EMBEDDING_MODEL_NAME}".replace(
    "-", "_"
)

POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PWD = os.environ["POSTGRES_PWD"]
POSTGRES_DB = os.environ["POSTGRES_DB"]
POSTGRES_HOST = os.environ["POSTGRES_HOST"]
POSTGRES_PORT = os.environ["POSTGRES_PORT"]

GROQ_API_KEY = os.environ["GROQ_API_KEY"]

LLM_MODEL: Final = "groq"
LLM_MODEL_PARAMS = GroqParams(api_key=GROQ_API_KEY, model="llama-3.1-70b-versatile")

RETRIEVAL_METHOD: Final = "pg_semantic_abstract+article"

client = Groq(api_key=GROQ_API_KEY)

# Open connection to database
postgres_connection_params = PostgresParams(
    host=POSTGRES_HOST,
    port=POSTGRES_PORT,
    user=POSTGRES_USER,
    pwd=POSTGRES_PWD,
    database=POSTGRES_DB,
)


@st.cache_resource
def open_connection():
    conn = open_db_connection(
        connection_params=postgres_connection_params, autocommit=True
    )
    return conn


conn = open_connection()

st.header(
    "ragXiv - Chat with quantitative finance papers", divider="grey", anchor=False
)


# Initialize chat history and user feedback
if "messages" not in st.session_state:
    st.session_state.messages = []

if "feedback" not in st.session_state:
    st.session_state.feedback = []

if "question_state" not in st.session_state:
    st.session_state.question_state = False

if "response" not in st.session_state:
    st.session_state.response = None

if "user_feedback" not in st.session_state:
    st.session_state.user_feedback = None


def fbcb():
    # Callback function
    print(st.session_state.response)


# Display chat messages from history on app rerun
for message in st.session_state.messages:
    avatar = "🤖" if message["role"] == "assistant" else "👨‍💻"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])


def build_user_feedback(
    user_question: str, system_answer: str, references: List[str], satisfied: bool
) -> dict:
    user_feedback = {
        "timestamp": datetime.now(),
        "user_question": user_question,
        "answer": system_answer,
        "references": references,
        "satisfied": satisfied,
    }
    return user_feedback


def generate_chat_responses(chat_completion) -> Generator[str, None, None]:
    """Yield chat response content from the Groq API response."""
    for chunk in chat_completion:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


user_query = st.chat_input("Enter your prompt here...")
if user_query:
    st.session_state.question_state = True

if st.session_state.question_state:
    st.session_state.messages.append({"role": "user", "content": user_query})

    with st.chat_message("user", avatar="👨‍💻"):
        st.markdown(user_query)

    # Fetch response from Groq API
    with st.spinner(""):
        try:
            # Search and retrieve relevant document
            semantic_search_abstract = SemanticSearch(
                query=user_query,
                table=TABLE_EMBEDDING_ABSTRACT,
                similarity_metric="<#>",
                embedding_model=EMBEDDING_MODEL_NAME,
                max_documents=3,
            )

            semantic_search_article = SemanticSearch(
                query=user_query,
                table=TABLE_EMBEDDING_ARTICLE,
                similarity_metric="<#>",
                embedding_model=EMBEDDING_MODEL_NAME,
                max_documents=3,
            )

            semantic_search_hierarchy = [
                semantic_search_abstract,
                semantic_search_article,
            ]

            relevant_documents = retrieve_similar_documents(
                conn=conn,
                retrieval_method=RETRIEVAL_METHOD,
                retrieval_parameters=semantic_search_hierarchy,
            )
            prompt = build_rag_prompt(
                user_question=relevant_documents["question"],
                context=relevant_documents["documents"],
            )

            chat_completion = client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )

            # Define string with suggested papers
            references_response = f"""
            If you would like to learn more about the topic, I suggest you refer to the following papers: \n\n
{'\n'.join([f'- {url}' for url in relevant_documents['references']])}"""

            # Use the generator function with st.write_stream
            with st.chat_message("assistant", avatar="🤖"):
                chat_responses_generator = generate_chat_responses(chat_completion)
                full_response = st.write_stream(chat_responses_generator)
        except Exception as e:
            st.error(e, icon="🚨")

    # Append the full response to session_state.messages
    if isinstance(full_response, str):
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )
    else:
        # Handle the case where full_response is not a string
        combined_response = "\n".join(str(item) for item in full_response)
        st.session_state.messages.append(
            {"role": "assistant", "content": combined_response}
        )

    # Display chat messages from history once references have been added
    st.session_state.messages.append(
        {"role": "assistant", "content": references_response}
    )

    # Display chat messages from history on app rerun
    message = st.session_state.messages[-1]
    avatar = "🤖" if message["role"] == "assistant" else "👨‍💻"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

    # Add thumbs up / thumbs down buttons
    response = st.feedback("thumbs", on_change=fbcb, key="response")

    # Capture feedback details
    user_feedback = build_user_feedback(
        user_question=user_query,
        system_answer=full_response,
        references=relevant_documents["references"],
        satisfied=response,
    )
    st.session_state.user_feedback = user_feedback

    st.session_state.question_state = False


if st.session_state.response is not None:
    # Set correct user feedback selection
    st.session_state.user_feedback["response"] = st.session_state.response
    print(st.session_state.user_feedback)

    # Now it can be stored in a database (or appended to a list)
    st.session_state.feedback.append(st.session_state.user_feedback)
    print(st.session_state.feedback)
