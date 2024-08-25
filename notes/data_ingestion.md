# Data ingestion

## Obtaining papers from arXiv

- Academic papers are retrieved from [arXiv](https://arxiv.org) using the [`arxiv` library](http://lukasschwab.me/arxiv.py/arxiv.html)
- Some examples about the Search function:
    - Search last 10 papers that **contain a keyword**:
        ```python
        # Search for the 10 most recent articles matching the keyword "quantum."
        search = arxiv.Search(
            query = "quantum",
            max_results = 10,
            sort_by = SortCriterion.SubmittedDate
        )
        ```
    - **Advanced searching** (use [arXiv API manual for reference](https://arxiv.org/help/api/user-manual#query_details)):
        ```python
        search = arxiv.Search(query = "au:del_maestro AND ti:checkerboard")
        ```
    - Retrieve paper **by ID**:
        ```python
        search_by_id = Search(id_list=["1605.08386v1"])
        ```
- It seems that [this undocumented API feature](https://groups.google.com/g/arxiv-api/c/mAFYT2VRpK0?pli=1) can be used to filter by specific dates, but there is not clear method to filter between a range of dates.


## Parsing papers

- Instead of parsing the raw content of pdfs, we will use the html versions of the papers
- HTML versions of arXiv papers [started on 01/12/2023](https://arxiv.org/html/2402.08954v1), so this POC will only use papers from that date onwards.
- Processing:
    - HTML versions of arXiv papers contain the main body as the `<article>` tag
    - Class `ltx_authors` contains the authors, which has already been retrieved as metadata and is not relevant information for the RAG system, so it is deleted.
    - Class `ltx_bibliography` contains the bibliography, not relevant for the RAG system, so it is deleted.
    - Class `ltx_figure` contains figures, which cannot be used in our RAG system as it is, so they are deleted.
    - Class `ltx_appendix` contains appendices, which usually contain math and theorems' proofs, not relevant for the RAG system.
    - Math equations are removed, from class `ltx_equation` and tag `<math>`.
- Once the html has been retrieved it is processed until is converted to a more readable content, such as markdown. [Library `markdownify`](https://python.langchain.com/v0.2/docs/integrations/document_transformers/markdownify/) is used for this task.


## Chunking

- Before creating the embeddings for each article, the content must be split into chunks.
- Valid chunking methods should be included in `ragxiv.embedding.ChunkMethod`
- A initial proof-of-concept will be obtained using `langchain`'s `MarkdownTextSplitter`, a basic `RecursiveCharacterTextSplitter` adapter for Markdown formatting. It tries to keep the paragraph, then the sentences and then the words together as long as possible; Hence prioritizes keeping related information together.
- Once the retrieval system has been implemented, other advanced alternatives can be further analyzed, such as **Tokenizer Based Splitting** (using `nltk` or `spacy` libraries), or even **Sematic Similarity Based** splitting. Another chunking method is **Propositions Based Splitting**[(detailed in this paper)](https://arxiv.org/pdf/2312.06648.pdf), which utilizes LLM to create chunks by converting paragraphs into multiple list of propositions which are then stored as chunks.
- The embedding model's maximum chunk size must be taken into account when splitting the article. For `sentence-transformer` models, the maximum chunk size is listed [here](https://www.sbert.net/docs/sentence_transformer/pretrained_models.html#model-overview)

Resources:
- [Chunking strategies](https://medium.com/@rahulpant.me/chunking-text-splitting-strategies-llms-579ab4ede2eb)
- [5 levels of text splitting](https://github.com/FullStackRetrieval-com/RetrievalTutorials/blob/main/tutorials/LevelsOfTextSplitting/5_Levels_Of_Text_Splitting.ipynb)
- [Splitting html files and saving chunks using langchain](https://stackoverflow.com/questions/78481278/splitting-html-file-and-saving-chunks-using-langchain)
- [Pinecone's chunking considerations](https://www.pinecone.io/learn/chunking-strategies/)


## Embeddings

- Valid embedding models should be included in `ragxiv.embedding.EmbeddingModel`

Resources:
- [Sentence transformers models overview](https://www.sbert.net/docs/sentence_transformer/pretrained_models.html#model-overview)
- [Sentence transformers in HuggingFace](https://huggingface.co/docs/hub/sentence-transformers)


# Postgres as a vector database

## Postgres setup

- We will run postgres inside a docker container, using this command:

    ```bash
    docker run -d \
        --name postgres \
        -e POSTGRES_PASSWORD=mysecretpassword \
        -v /volume_postgres:/var/lib/postgresql/data \
        -p 5432:5432 \
        ankane/pgvector
    ```

    - The password for this instance is set to `mysecretpassword`
    - The `ankane/pgvector` Docker image includes both PostgreSQL and the `pgvector` extension.

- Once the PostgreSQL instance with pgvector is running, I need to enable the extension for the database `ragxiv_db` (this can be done either by command line interface or by a Python script):
    - Access the PostgreSQL Container:
    ```bash
    docker exec -it postgres psql -U postgres
    ```
    - Create a Database (if not already done):
    ```sql
    CREATE DATABASE ragxiv_db;
    ```
    - Connect to the Database:
    ```sql
    \c ragxiv_db;
    ```
    - Enable the pgvector Extension:
    ```sql
    CREATE EXTENSION vector;
    ```
 Resources
 - [Hybrid search in pg_vector](https://github.com/pgvector/pgvector-python/blob/master/examples/hybrid_search.py#L46)
