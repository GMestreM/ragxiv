"""Retrieve similar documents from database"""

from typing import List, Literal, TypedDict, Union, Optional, Any, get_args
import psycopg
from ragxiv.database import (
    SemanticSearch,
    semantic_search_postgres,
    keyword_search_postgres,
    TextSearch,
)

RetrievalMethod = Literal[
    "pg_semantic_abstract+article",
    "pg_semantic_article",
    "pg_text_article",
]
RetrievalParameters = Union[SemanticSearch, TextSearch]


class RelevantDocuments(TypedDict):
    question: str
    documents: List[str]
    references: List[str]


def retrieve_similar_documents(
    retrieval_method: RetrievalMethod | str,
    retrieval_parameters: List[Any],
    conn: Optional[psycopg.Connection],
) -> RelevantDocuments:
    if retrieval_method == "pg_semantic_abstract+article":
        if isinstance(conn, psycopg.Connection):
            relevant_documents = pg_semantic_retrieval_hierarchical(
                conn=conn, retrieval_parameters=retrieval_parameters
            )
        else:
            raise ValueError("Database connection not opened")
    elif retrieval_method == "pg_semantic_article":
        if isinstance(conn, psycopg.Connection):
            relevant_documents = pg_semantic_retrieval(
                conn=conn, retrieval_parameters=retrieval_parameters
            )
        else:
            raise ValueError("Database connection not opened")
    elif retrieval_method == "pg_text_article":
        if isinstance(conn, psycopg.Connection):
            relevant_documents = pg_text_retrieval(
                conn=conn, retrieval_parameters=retrieval_parameters
            )
        else:
            raise ValueError("Database connection not opened")
    else:
        raise ValueError(f"Retrieval method {retrieval_method} not implemented")
    return relevant_documents


def pg_semantic_retrieval_hierarchical(
    conn: psycopg.Connection, retrieval_parameters: List[SemanticSearch]
) -> RelevantDocuments:
    if conn:
        # Semantic search on abstracts
        semantic_search_abstract = retrieval_parameters[0]
        semantic_search_results_abstract, question_embedding = semantic_search_postgres(
            conn=conn,
            semantic_search_params=semantic_search_abstract,
        )

        # Get ID of relevant documents
        id_relevant_documents = [
            result[0] for result in semantic_search_results_abstract
        ]

        # Semantic search on articles filtered by ID
        semantic_search_article = retrieval_parameters[1]
        semantic_search_results_articles, _ = semantic_search_postgres(
            conn=conn,
            semantic_search_params=semantic_search_article,
            filter_id=id_relevant_documents,
        )

        # Prepare output
        final_documents = [
            document[1] for document in semantic_search_results_abstract
        ] + [document[1] for document in semantic_search_results_articles]
        relevant_documents = RelevantDocuments(
            question=semantic_search_abstract["query"],
            documents=final_documents,
            references=id_relevant_documents,
        )
    else:
        raise ValueError("Database connection not opened")
    return relevant_documents


def pg_semantic_retrieval(
    conn: psycopg.Connection, retrieval_parameters: List[SemanticSearch]
) -> RelevantDocuments:
    if conn:
        # Semantic search on articles
        semantic_search_article = retrieval_parameters[0]
        semantic_search_results_article, question_embedding = semantic_search_postgres(
            conn=conn,
            semantic_search_params=semantic_search_article,
        )

        # Get ID of relevant documents
        id_relevant_documents = [
            result[0] for result in semantic_search_results_article
        ]

        # Prepare output
        final_documents = [document[1] for document in semantic_search_results_article]

        relevant_documents = RelevantDocuments(
            question=semantic_search_article["query"],
            documents=final_documents,
            references=id_relevant_documents,
        )
    else:
        raise ValueError("Database connection not opened")
    return relevant_documents


def pg_text_retrieval(
    conn: psycopg.Connection, retrieval_parameters: List[TextSearch]
) -> RelevantDocuments:
    if conn:
        # Text search on articles
        text_search_article = retrieval_parameters[0]
        text_search_results_article = keyword_search_postgres(
            conn=conn,
            text_search_params=text_search_article,
        )

        # Get ID of relevant documents
        id_relevant_documents = [result[0] for result in text_search_results_article]

        # Prepare output
        final_documents = [document[1] for document in text_search_results_article]

        relevant_documents = RelevantDocuments(
            question=text_search_article["query"],
            documents=final_documents,
            references=id_relevant_documents,
        )
    else:
        raise ValueError("Database connection not opened")
    return relevant_documents
