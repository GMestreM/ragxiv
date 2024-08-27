"""Simple example of the RAG flow implementation"""

import os
import sys
from dotenv import load_dotenv
import pandas as pd
from typing import Final

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ragxiv.database import (
    open_db_connection,
    PostgresParams,
    SemanticSearch,
)
from ragxiv.retrieval import retrieve_similar_documents
from ragxiv.llm import llm_chat_completion, GroqParams

load_dotenv("./.env")

# Define user question
user_question = "How detect trend (or momentum) in financial assets?"
print(f"\n - QUESTION: {user_question}\n")

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

# Open connection to database
postgres_connection_params = PostgresParams(
    host=POSTGRES_HOST,
    port=POSTGRES_PORT,
    user=POSTGRES_USER,
    pwd=POSTGRES_PWD,
    database=POSTGRES_DB,
)

conn = open_db_connection(connection_params=postgres_connection_params, autocommit=True)

# Search and retrieve relevant document
semantic_search_abstract = SemanticSearch(
    query=user_question,
    table=TABLE_EMBEDDING_ABSTRACT,
    similarity_metric="<#>",
    embedding_model=EMBEDDING_MODEL_NAME,
    max_documents=3,
)

semantic_search_article = SemanticSearch(
    query=user_question,
    table=TABLE_EMBEDDING_ARTICLE,
    similarity_metric="<#>",
    embedding_model=EMBEDDING_MODEL_NAME,
    max_documents=3,
)

semantic_search_hierarchy = [semantic_search_abstract, semantic_search_article]

relevant_documents = retrieve_similar_documents(
    conn=conn,
    retrieval_method=RETRIEVAL_METHOD,
    retrieval_parameters=semantic_search_hierarchy,
)

# Create prompt
prompt = f"""
You are an expert in quantitative finance. Answer QUESTION but limit your information to what is inside CONTEXT.

QUESTION: {relevant_documents['question']}

CONTEXT: {' \n\n '.join([f"{ document} " for document in relevant_documents["documents"]])}
"""

# Generation
response = llm_chat_completion(
    query=prompt, llm_model=LLM_MODEL, llm_parameters=LLM_MODEL_PARAMS
)

print(f"\n - ANSWER: {response['response']}")
