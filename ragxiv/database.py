"""Interact with PostgreSQL database"""

import re
import datetime
import psycopg
from pgvector.psycopg import register_vector
from typing import List, Literal, Optional, TypedDict
from sentence_transformers import SentenceTransformer
from ragxiv.embedding import PaperEmbedding


class PostgresParams(TypedDict):
    host: str
    port: str
    user: str
    pwd: str
    database: str


class SemanticSearch(TypedDict):
    query: str
    table: str
    similarity_metric: Literal["<#>", "<=>", "<->", "<+>"]
    embedding_model: str | SentenceTransformer
    max_documents: int


class TextSearch(TypedDict):
    query: str
    table: str
    max_documents: int


class UserFeedback(TypedDict):
    user_id: str
    question: str
    answer: str
    thumbs: Optional[int]
    documents_retrieved: Optional[str]
    similarity: Optional[float]
    relevance: Optional[str]
    llm_model: Optional[str]
    embedding_model: Optional[str]
    elapsed_time: Optional[datetime.timedelta]
    feedback_timestamp: Optional[datetime.datetime]


def open_db_connection(
    connection_params: PostgresParams, autocommit: bool = True
) -> psycopg.Connection | None:
    """Open connection to PostgreSQL database

    Args:
        connection_params (PostgresParams): Connection parameters for
            opening connection to PostgreSQL database
        autocommit (bool, optional): Wether to create connection using
            autocommit model. Commands have immediate effect.
            Defaults to True.

    Returns:
        psycopg.Connection | None: Either a connection to the database
            or None if unable to create connection
    """
    conn = psycopg.connect(
        host=connection_params["host"],
        port=connection_params["port"],
        user=connection_params["user"],
        password=connection_params["pwd"],
        dbname=connection_params["database"],
        autocommit=autocommit,
    )
    try:
        curs = conn.cursor()

        # Execute an SQL query to test connection
        curs.execute("SELECT version();")
        db_version = curs.fetchone()
        print(f"Connected to - {db_version}")
        curs.close()
    except (Exception, psycopg.DatabaseError) as error:
        print(f"Error while connecting to PostgreSQL: {error}")
        conn = None
    return conn


def create_embedding_table(
    conn: psycopg.Connection, table_name: str, embedding_dimension: int
):
    """
    Create a table for storing both text and vector embeddings

    The table contains the following fields:
    - article_id: string that specified the identified of the paper
    - content: string that contains the raw text
    - embedding: vector that contains the embedding of the raw text

    Args:
        conn (psycopg.Connection): Connection to the database
        table_name (str): Name of the table to be created. It should follow
            the following structure: 'embedding_<type>_<model_name>', where
            <type> is either 'abstract' or 'article' and <model_name> is
            the name of the embedding model used.
        embedding_dimension (int): Integer specifying the dimension of
            the embedding vectors
    """
    # Execute create table statement
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id bigserial PRIMARY KEY,
        article_id text,
        content text,
        embedding vector({embedding_dimension})
    )"""
    conn.execute(create_sql)

    # Execute create index statement
    index_sql = f"""
    CREATE INDEX ON {table_name} USING GIN (to_tsvector('english', content))
    """
    conn.execute(index_sql)

    # Register pg_vector vector
    register_vector(conn)


def create_user_feedback_table(
    conn: psycopg.Connection, table_name: str = "user_feedback"
):

    # Execute create table statement
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        feedback_id SERIAL PRIMARY KEY,            -- Unique identifier for each feedback entry
        unique_user_id VARCHAR(255) NOT NULL,      -- Unique identifier for the user
        user_question TEXT NOT NULL,               -- The question asked by the user
        answer TEXT NOT NULL,                      -- The answer generated by the system
        thumbs SMALLINT,                           -- User rating: -1 for thumbs down, 1 for thumbs up, or NULL if not provided
        documents_retrieved TEXT,                  -- A list of document identifiers or titles retrieved for the query
        similarity FLOAT,                          -- Similarity score between the query and retrieved documents
        relevance TEXT,                            -- User's feedback on the relevance of the answer
        llm_model VARCHAR(255),                    -- Name of the LLM model used to generate the answer
        embedding_model VARCHAR(255),              -- Name of the embedding model used for document retrieval
        elapsed_time INTERVAL,                     -- Time elapsed between user query and LLM response
        feedback_timestamp TIMESTAMP DEFAULT NOW() -- Timestamp when the feedback was submitted
    )"""
    conn.execute(create_sql)


def insert_embedding_data(
    conn: psycopg.Connection, table_name: str, paper_embedding: List[PaperEmbedding]
):
    """Insert paper embeddings into a PostgreSQL table

    Args:
        conn (psycopg.Connection): Connection to the database
        table_name (str): Table name where data will be inserted.
        paper_embedding (List[PaperEmbedding]): List of paper embeddings
            that will be stored in the database
    """
    register_vector(conn)

    # Insert values sequentially
    with conn.cursor() as curs:
        for row in paper_embedding:
            curs.execute(
                f"INSERT INTO {table_name} (article_id, content, embedding) VALUES (%s, %s, %s)",
                (row["id"], row["content"], row["embeddings"]),
            )


def insert_user_feedback(
    conn: psycopg.Connection, feedback: UserFeedback, table_name: str = "user_feedback"
):
    """
    Insert a new record into the user_feedback table.

    Parameters:
        conn (psycopg.Connection): Connection object to the PostgreSQL database.
        feedback (UserFeedback): Instance of UserFeedback containing feedback data.
        table_name (str): The name of the table where the feedback will be inserted (default is 'user_feedback').
    """

    insert_sql = f"""
    INSERT INTO {table_name} (
        unique_user_id, user_question, answer, thumbs, documents_retrieved, similarity, relevance,
        llm_model, embedding_model, elapsed_time, feedback_timestamp
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    # Use feedback data to populate SQL parameters
    with conn.cursor() as cursor:
        cursor.execute(
            insert_sql,
            (
                feedback["user_id"],
                feedback["question"],
                feedback["answer"],
                feedback["thumbs"],
                feedback["documents_retrieved"],
                feedback["similarity"],
                feedback["relevance"],
                feedback["llm_model"],
                feedback["embedding_model"],
                feedback["elapsed_time"],
                feedback["feedback_timestamp"]
                or datetime.datetime.now(),  # Use current time if not provided
            ),
        )
        conn.commit()  # Commit the transaction to save the changes


def get_article_id_data(conn: psycopg.Connection, table_name: str) -> List[str]:
    """Get article ids already present in the database

    Args:
        conn (psycopg.Connection): Connection to the database
        table_name (str): Table name where data will be inserted.
        paper_embedding (List[PaperEmbedding]): List of paper embeddings
            that will be stored in the database

    Returns:
        List[str]: List of strings containing the different
            document ids
    """
    with conn.cursor() as curs:
        query = f"SELECT DISTINCT article_id FROM {table_name}"
        curs.execute(query)
        data = curs.fetchall()

        # Format as list of strings
        document_ids = [docs[0] for docs in data]
        return document_ids


def semantic_search_postgres(
    conn: psycopg.Connection,
    semantic_search_params: SemanticSearch,
    filter_id: Optional[List[str]] = None,
):
    # Cosine distance: <#>
    # negative inner product: <=>
    # L2 distance: <->
    # L1 distance: <+>
    embedding_model = semantic_search_params["embedding_model"]
    if isinstance(embedding_model, str):
        from sentence_transformers import SentenceTransformer

        try:
            embedding_model = SentenceTransformer(embedding_model)
        except Exception as e:
            print(e)
            raise ValueError(f"Unable to load embedding model {embedding_model}")
    query = semantic_search_params["query"]
    table_name = semantic_search_params["table"]
    max_documents = semantic_search_params["max_documents"]
    similarity_metric = semantic_search_params["similarity_metric"]

    query_embedding = embedding_model.encode(query)

    register_vector(conn)

    filter_id_query = ""
    if filter_id:
        fields = ", ".join([f"'{w}'" for w in filter_id])
        filter_id_query = f" WHERE article_id IN ({fields})"

    with conn.cursor() as cur:
        cur.execute(
            f"SELECT article_id, content, embedding FROM {table_name} {filter_id_query} ORDER BY embedding {similarity_metric} %s LIMIT {max_documents}",
            (query_embedding,),
        )
        return cur.fetchall(), query_embedding


def keyword_search_postgres(conn: psycopg.Connection, text_search_params: TextSearch):
    """Not very useful keyword search (same weight to each word)"""

    query = text_search_params["query"]
    table_name = text_search_params["table"]
    max_documents = text_search_params["max_documents"]

    # Sanitize query: remove invalid characters and sanitize the input for to_tsquery
    query = re.sub(r"[^a-zA-Z0-9\s]", "", query)
    # query = re.sub(r'\s+', ' & ', query)  # Replace spaces with `&` for AND

    query_use = query.replace(" ", " | ")

    # Remove the trailing operator (and other redundant ones)
    query_use = re.sub(r"\|\s*$", "", query_use)  # Remove trailing `|`
    query_use = query_use.replace(" |  | ", " | ")
    # query_use = re.sub(r'\s*\|\s*', ' | ', query_use)  # Ensure correct spacing around `|`

    with conn.cursor() as cur:
        cur.execute(
            f"SELECT article_id, content, embedding FROM {table_name}, to_tsquery('english', %s) query WHERE to_tsvector('english', content) @@ query ORDER BY ts_rank_cd(to_tsvector('english', content), query) DESC LIMIT {max_documents}",
            (query_use,),
        )
        return cur.fetchall()
