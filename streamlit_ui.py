"""Simple streamlit frontend"""

import os
import sys
import uuid
import time
from dotenv import load_dotenv, dotenv_values
from typing import List, Final, Generator, Optional
from datetime import datetime, timedelta
import streamlit as st

from ragxiv.database import (
    open_db_connection,
    PostgresParams,
    SemanticSearch,
    UserFeedback,
    insert_user_feedback,
)
from ragxiv.retrieval import retrieve_similar_documents
from ragxiv.llm import llm_chat_completion, GroqParams, build_rag_prompt
from ragxiv.config import get_config

from groq import Groq

load_dotenv(".env")

config = get_config()
if config:
    config_ingestion = config["ingestion"]
    config_rag = config["rag"]

st.set_page_config(
    page_icon="💬",
    layout="wide",
    page_title="ragXiv - Retrieval-Augmented Generation with arXiv knowledge-base",
)

# Set variables
EMBEDDING_MODEL_NAME: Final = config_ingestion["embedding_model_name"]
TABLE_EMBEDDING_ARTICLE = f"embedding_article_{EMBEDDING_MODEL_NAME}".replace("-", "_")
TABLE_EMBEDDING_ABSTRACT = f"embedding_abstract_{EMBEDDING_MODEL_NAME}".replace(
    "-", "_"
)
GROQ_API_KEY = os.environ["GROQ_API_KEY"]

LLM_MODEL: Final = "groq"
LLM_MODEL_PARAMS = GroqParams(api_key=GROQ_API_KEY, model=config_rag["llm_model"])
RETRIEVAL_METHOD: Final = config_rag["retrieval_method"]

postgres_connection_params = PostgresParams(
    host=os.environ["POSTGRES_HOST"],
    port=os.environ["POSTGRES_PORT"],
    user=os.environ["POSTGRES_USER"],
    pwd=os.environ["POSTGRES_PWD"],
    database=os.environ["POSTGRES_DB"],
)

client = Groq(api_key=GROQ_API_KEY)


@st.cache_resource
def open_connection():
    conn = open_db_connection(
        connection_params=postgres_connection_params, autocommit=True
    )
    return conn


@st.cache_resource
def create_unique_id() -> str:
    unique_id = str(uuid.uuid4())  # Generate a UUID
    return unique_id


unique_id = create_unique_id()
conn = open_connection()

# Streamlit app
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
    user_question: str,
    system_answer: str,
    references: Optional[str] = None,
    satisfied: Optional[int] = None,
    elapsed_time: Optional[timedelta] = None,
    feedback_timestamp: Optional[datetime] = datetime.now(),
) -> UserFeedback:
    user_feedback = UserFeedback(
        user_id=unique_id,
        question=user_question,
        answer=system_answer,
        thumbs=satisfied,
        documents_retrieved=references,
        similarity=None,
        relevance=None,
        llm_model=None,
        embedding_model=None,
        elapsed_time=elapsed_time,
        feedback_timestamp=feedback_timestamp,
    )
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
    ini_time = datetime.now()

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
                model=config_rag["llm_model"],
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )

            # Define string with suggested papers
            references_response = f"""
If you would like to learn more about the topic, I suggest you refer to the following papers: \n\n
""" + "\n".join(
                [f"- {url}" for url in relevant_documents["references"]]
            )
            print(references_response)

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
    end_time = datetime.now()

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
        references=";".join(relevant_documents["references"]),
        satisfied=response,
        elapsed_time=end_time - ini_time,
    )
    st.session_state.user_feedback = user_feedback

    st.session_state.question_state = False


if st.session_state.response is not None:
    # Set correct user feedback selection
    st.session_state.user_feedback["response"] = st.session_state.response
    print(st.session_state.user_feedback)

    # Now it can be stored in a database (or appended to a list)
    insert_user_feedback(conn=conn, feedback=st.session_state.user_feedback)

    st.session_state.feedback.append(st.session_state.user_feedback)
    print(st.session_state.feedback)
