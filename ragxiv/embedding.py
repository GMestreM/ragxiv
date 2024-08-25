"""Chunk documents and obtain embeddings"""

from tqdm.auto import tqdm
from typing import List, Literal, TypedDict, get_args
import numpy as np
from langchain.text_splitter import MarkdownTextSplitter
from sentence_transformers import SentenceTransformer
from ragxiv.utils import normalize_vector


# Default embedding parameters
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNK_METHOD = "MarkdownTextSplitter"
EMBEDDING_MODEL_NAME = "multi-qa-mpnet-base-dot-v1"

ChunkMethod = Literal["MarkdownTextSplitter"]
SentenceTransformerModels = Literal["multi-qa-mpnet-base-dot-v1",]
EmbeddingModel = Literal[SentenceTransformerModels]


class ChunkParams(TypedDict):
    method: ChunkMethod
    size: int
    overlap: int


class Embedding(TypedDict):
    model: EmbeddingModel
    dimension: int
    content: List[str]
    embedding: np.ndarray


class PaperEmbedding(TypedDict):
    id: str
    content: str
    embeddings: np.ndarray


def chunk_document(document: str, chunk_params: ChunkParams) -> List[str]:
    """Split a given document using the selected method

    Args:
        document (str): Markdown text of a document
        chunk_params (ChunkParams): Specification of the chunking
            method that will be used

    Raises:
        ValueError: The selected chunk method has not been
            implemented yet

    Returns:
        List[str]: List of strings containing the different
            document chunks
    """
    if chunk_params["method"] == "MarkdownTextSplitter":
        chunks = chunk_markdown_recursive(document=document, chunk_params=chunk_params)
    else:
        raise ValueError(f"ChunkMethod {chunk_params['method']} not implemented")
    return chunks


def chunk_markdown_recursive(document: str, chunk_params: ChunkParams) -> List[str]:
    """Recursive Character Text Splitter using Markdown separators

    Args:
        document (str): Markdown text of a document
        chunk_params (ChunkParams): Specification of the chunking
            method that will be used
    Returns:
        List[str]: List of strings containing the different
            document chunks
    """
    chunk_size = chunk_params["size"]
    chunk_overlap = chunk_params["overlap"]

    # Initialize splitter
    splitter = MarkdownTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    chunks = splitter.create_documents([document])

    # To list of strings
    chunks = [chunk.page_content for chunk in chunks]

    return chunks


def document_embedding(chunks: List[str], embedding_model: EmbeddingModel) -> Embedding:
    """Create a vector embedding for a list of document chunks

    Args:
        chunks (List[str]): List of strings containing the different
            document chunks
        embedding_model (EmbeddingModel): Name of the embedding model

    Raises:
        ValueError: The selected embedding method has not been
            implemented yet

    Returns:
        Embedding: Normalized vector embedding as an np.array together with
            the original chunks and model details

    """
    if embedding_model in get_args(SentenceTransformerModels):
        embedding = document_embedding_sentence_transformers(
            chunks=chunks, embedding_model=embedding_model
        )
    else:
        raise ValueError(f"EmbeddingModel {embedding_model} not implemented")
    return embedding


def document_embedding_sentence_transformers(
    chunks: List[str], embedding_model: EmbeddingModel
) -> Embedding:
    """Sentence Transformer embedding

    Args:
        chunks (List[str]): List of strings containing the different
            document chunks
        embedding_model (EmbeddingModel): Name of the embedding model

    Returns:
        Embedding: Normalized vector embedding as an np.array together with
            the original chunks and model details
    """
    # Initialize embedding
    embedding_transformer = SentenceTransformer(embedding_model)
    word_embedding_dimension = embedding_transformer.get_sentence_embedding_dimension()

    document_embeddings = np.empty(shape=(0, word_embedding_dimension))
    for chunk in tqdm(chunks, total=len(chunks)):
        chunk_embedding = embedding_transformer.encode(chunk)
        chunk_embedding = normalize_vector(chunk_embedding)
        document_embeddings = np.vstack((document_embeddings, chunk_embedding))

    embedding = Embedding(
        model=embedding_transformer,
        dimension=word_embedding_dimension,
        content=chunks,
        embedding=document_embeddings,
    )
    return embedding
