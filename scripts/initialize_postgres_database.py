"""
Initialize database, create tables and populate them with document embeddings

This script assumes that get_arxiv_metadata.py and get_markdown_papers.py
have been executed
"""

import os
import sys
from dotenv import load_dotenv
import pandas as pd
from tqdm.auto import tqdm
from typing import Final

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ragxiv.database import (
    open_db_connection,
    create_embedding_table,
    insert_embedding_data,
    PostgresParams,
)
from ragxiv.embedding import (
    PaperEmbedding,
    ChunkParams,
    chunk_document,
    document_embedding,
)

load_dotenv("./.env")

# Default embedding parameters
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNK_METHOD: Final = "MarkdownTextSplitter"
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

METADATA_PATH = "metadata_all.csv"
MARKDOWN_ARTICLES_PATH = "article_markdown.csv"


postgres_connection_params = PostgresParams(
    host=POSTGRES_HOST,
    port=POSTGRES_PORT,
    user=POSTGRES_USER,
    pwd=POSTGRES_PWD,
    database=POSTGRES_DB,
)

# Load documents
metadata = pd.read_csv(METADATA_PATH, sep=";")
markdown_text = pd.read_csv(MARKDOWN_ARTICLES_PATH, sep=";")
# Filter metadata by id
metadata = metadata.loc[metadata["id"].isin(markdown_text["id"]), :]
metadata.set_index("id", inplace=True)
markdown_text.set_index("id", inplace=True)
markdown_text["abstract"] = metadata["summary"]
markdown_text.reset_index(inplace=True)
markdown_text.drop(columns=["Unnamed: 0"], inplace=True)
markdown_text = markdown_text.to_dict(orient="records")

# Create embeddings
chunk_parameters = ChunkParams(
    method=CHUNK_METHOD, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP
)

list_article_embeddings = []
list_abstract_embeddings = []
embedding_dimension = 0
for article in tqdm(markdown_text, total=len(markdown_text)):
    article_id = article["id"]
    document = article["article"]
    abstract = article["abstract"]

    # Chunk document
    document_chunks = chunk_document(document=document, chunk_params=chunk_parameters)

    # Document embedding
    article_embedding = document_embedding(
        chunks=document_chunks, embedding_model=EMBEDDING_MODEL_NAME
    )

    # Abstract embedding
    abstract_embedding = document_embedding(
        chunks=[abstract], embedding_model=EMBEDDING_MODEL_NAME
    )

    if embedding_dimension == 0:
        embedding_dimension = article_embedding["dimension"]

    # Format output
    for i in range(len(article_embedding["content"])):
        row_store = PaperEmbedding(
            id=article_id,
            content=article_embedding["content"][i],
            embeddings=article_embedding["embedding"][i, :],
        )
        list_article_embeddings.append(row_store)

    for i in range(len(abstract_embedding["content"])):
        row_store = PaperEmbedding(
            id=article_id,
            content=abstract_embedding["content"][i],
            embeddings=abstract_embedding["embedding"][i, :],
        )
        list_abstract_embeddings.append(row_store)


# Open connection to database
conn = open_db_connection(connection_params=postgres_connection_params, autocommit=True)

# Create schema
if conn:
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Drop tables if they already exist
    conn.execute(f"DROP TABLE IF EXISTS {TABLE_EMBEDDING_ARTICLE}")
    conn.execute(f"DROP TABLE IF EXISTS {TABLE_EMBEDDING_ABSTRACT}")

    # Create tables
    create_embedding_table(
        conn=conn,
        table_name=TABLE_EMBEDDING_ARTICLE,
        embedding_dimension=embedding_dimension,
    )
    create_embedding_table(
        conn=conn,
        table_name=TABLE_EMBEDDING_ABSTRACT,
        embedding_dimension=embedding_dimension,
    )

    # Insert data into tables
    insert_embedding_data(
        conn=conn,
        table_name=TABLE_EMBEDDING_ARTICLE,
        paper_embedding=list_article_embeddings,
    )
    insert_embedding_data(
        conn=conn,
        table_name=TABLE_EMBEDDING_ABSTRACT,
        paper_embedding=list_abstract_embeddings,
    )
