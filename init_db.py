"""Initialize database"""

import os
import sys
from typing import Final
from sentence_transformers import SentenceTransformer

from ragxiv.database import (
    open_db_connection,
    create_embedding_table,
    PostgresParams,
)

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

# Get embedding model info
embedding_transformer = SentenceTransformer(EMBEDDING_MODEL_NAME)
word_embedding_dimension = embedding_transformer.get_sentence_embedding_dimension()

postgres_connection_params = PostgresParams(
    host=POSTGRES_HOST,
    port=POSTGRES_PORT,
    user=POSTGRES_USER,
    pwd=POSTGRES_PWD,
    database=POSTGRES_DB,
)

conn = open_db_connection(connection_params=postgres_connection_params, autocommit=True)

# Create schema
if conn:
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

    conn.execute(f"DROP TABLE IF EXISTS {TABLE_EMBEDDING_ARTICLE}")
    conn.execute(f"DROP TABLE IF EXISTS {TABLE_EMBEDDING_ABSTRACT}")

    # Create tables
    create_embedding_table(
        conn=conn,
        table_name=TABLE_EMBEDDING_ARTICLE,
        embedding_dimension=word_embedding_dimension,
    )
    create_embedding_table(
        conn=conn,
        table_name=TABLE_EMBEDDING_ABSTRACT,
        embedding_dimension=word_embedding_dimension,
    )
    print("Database initialized")
else:
    print("Issue when initializing database")
