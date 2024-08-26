"""Interact with PostgreSQL database"""

import os
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
        filter_id_query = (
            f" WHERE article_id IN ({' , '.join(f"'{w}'" for w in filter_id)})"
        )

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

    query_use = query.replace(" ", " | ")
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT id, content FROM {table_name}, to_tsquery('english', %s) query WHERE to_tsvector('english', content) @@ query ORDER BY ts_rank_cd(to_tsvector('english', content), query) DESC LIMIT {max_documents}",
            (query_use,),
        )
        return cur.fetchall()
