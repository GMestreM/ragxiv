"""Add new articles to the vector database"""

import os
from dotenv import load_dotenv
from typing import Final
from tqdm.auto import tqdm
from ragxiv.database import (
    PostgresParams,
    get_article_id_data,
    open_db_connection,
    insert_embedding_data,
)
from ragxiv.ingest import retrieve_arxiv_metadata, paper_html_to_markdown
from ragxiv.embedding import (
    PaperEmbedding,
    ChunkParams,
    chunk_document,
    document_embedding,
)
from ragxiv.config import get_config

load_dotenv(".env")
config = get_config()
if config:
    config_ingestion = config["ingestion"]

MAX_RESULTS_ARXIV = config_ingestion["max_documents_arxiv"]
CHUNK_SIZE = config_ingestion["chunk_size"]
CHUNK_OVERLAP = config_ingestion["chunk_overlap"]
CHUNK_METHOD: Final = config_ingestion["chunk_method"]
EMBEDDING_MODEL_NAME: Final = config_ingestion["embedding_model_name"]
TABLE_EMBEDDING_ARTICLE = f"embedding_article_{EMBEDDING_MODEL_NAME}".replace("-", "_")
TABLE_EMBEDDING_ABSTRACT = f"embedding_abstract_{EMBEDDING_MODEL_NAME}".replace(
    "-", "_"
)

# Open connection to database
postgres_connection_params = PostgresParams(
    host=os.environ["POSTGRES_HOST"],
    port=os.environ["POSTGRES_PORT"],
    user=os.environ["POSTGRES_USER"],
    pwd=os.environ["POSTGRES_PWD"],
    database=os.environ["POSTGRES_DB"],
)
conn = open_db_connection(connection_params=postgres_connection_params, autocommit=True)

if MAX_RESULTS_ARXIV > 0:
    # Get list of article ids already present in database
    article_ids_stored = get_article_id_data(
        conn=conn, table_name=TABLE_EMBEDDING_ARTICLE
    )

    # Fetch new papers from arxiv
    metadata = retrieve_arxiv_metadata(
        max_results=MAX_RESULTS_ARXIV, exclude_ids=article_ids_stored
    )

    # Process documents
    markdown_text = []
    for paper_id in tqdm(metadata, total=len(metadata)):
        article_markdown = paper_html_to_markdown(paper_id=paper_id, verbose=True)
        if article_markdown:
            dict_markdown = dict(id=paper_id["id"], article=article_markdown)
            dict_markdown["abstract"] = [
                meta["summary"] for meta in metadata if meta["id"] == paper_id["id"]
            ]
            markdown_text.append(dict_markdown)
        else:
            print(f"Unable to parse document {paper_id['id']}")

    # Chunk and embed documents
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
        document_chunks = chunk_document(
            document=document, chunk_params=chunk_parameters
        )

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

    # Store documents and embeddings in the database
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
