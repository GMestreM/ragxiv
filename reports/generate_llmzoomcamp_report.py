import os
import pandas as pd
from mdutils.mdutils import MdUtils

FILE_PATH = os.path.join("reports", "llm_zoomcamp_final_project_report")
RETRIEVAL_PATH = os.path.join("reports", "data", "comparison_retrieval_methods.csv")

mdFile = MdUtils(file_name=FILE_PATH, title="LLM Zoomcamp - Final Project report")

mdFile.new_paragraph(
    "ragXiv is my final project for the 2024 edition of the [LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp/). "
    "This report contains the different evaluation criteria for the projects, and illustrates how the project adresses them. "
)

mdFile.new_header(level=1, title="Evaluation criteria")
mdFile.new_header(level=2, title="Problem description")

mdFile.new_paragraph(
    "The problem that ragXiv tried to solve is described in detail at "
    "[the README.md file of this repository](https://github.com/GMestreM/ragxiv?tab=readme-ov-file#problem-statement) "
)

mdFile.new_header(level=2, title="RAG flow")
mdFile.new_paragraph(
    "As stated in the "
    "[project key features](https://github.com/GMestreM/ragxiv?tab=readme-ov-file#key-features), "
    "the RAG flow implemented in ragXiv employs:"
)
markdown_list = [
    "A **knowledge base** comprised of scholarly articles available at "
    "[arXiv](https://arxiv.org/), an open-access archive for academic papers. "
    "",
    "A **vector database** that uses PostgreSQL [`pg_vector` extension](https://github.com/pgvector/pgvector), "
    "which is used to store both the vector embeddings of the different documents as well as ",
    "to perform semantic search to retrieve only documents relevant for a given query.",
    "",
    "A **LLM model** that receives the extracted context from the knowledge base "
    "and is responsibe for generating clear, concise, and expert-level answers to user queries. "
    "",
]
mdFile.new_list(markdown_list)

mdFile.new_header(level=2, title="Retrieval evaluation")

mdFile.new_paragraph(
    "Different retrieval methods have been evalutated "
    "(check [script `evaluate_retrieval.py`](https://github.com/GMestreM/ragxiv/blob/main/scripts/evaluate_retrieval.py)): "
)
markdown_list = [
    "`pg_semantic_abstract+article`, which performs semantic search in "
    "two steps: first a semantic search is performed between the user query and the abstracts "
    "of academic papers; which narrows down the relevant documents and focuses on the most "
    "contextually aligned documents. Then, a second semantic search is executed, this time "
    "between the user's query and the body content of the selected papers. "
    "This ensures that the most pertinent sections of the papers are considered."
    "",
    "`pg_semantic_article` performs a single semantic search in the body content "
    "of all documents stored in the vector database."
    "",
    "`pg_text_article` perform a single keyword text search in the body"
    "content of all documents stored in the vector database. "
    "",
]
mdFile.new_list(markdown_list)
mdFile.new_paragraph(
    "The `hit_rate` and `mean_reciprocal_rank` measures have been used to "
    "compare the different retrieval methods. The table below shows the scores "
    "of each method:"
)
retrieval_metrics = pd.read_csv(RETRIEVAL_PATH, sep=";", index_col=[0])
mdFile.new_paragraph(retrieval_metrics.to_markdown())

mdFile.new_paragraph(
    "The best results are obtained with the **`pg_semantic_abstract+article`** "
    "method, so it will be used in the final application."
)

mdFile.new_header(level=2, title="RAG evaluation")

mdFile.new_paragraph("**TO-DO**")

mdFile.new_header(level=2, title="Interface")

mdFile.new_paragraph(
    "A Streamlit user interface has been build to ease the interaction with "
    "the application. It allows the user to interact with the RAG system using a "
    "chat interface, as illustrated in [this figure](https://github.com/GMestreM/ragxiv/tree/main?tab=readme-ov-file#overview)"
)

mdFile.new_header(level=2, title="Ingestion pipeline")

mdFile.new_paragraph(
    "ragXiv implements an automated ingestion pipeline, which retrieves "
    "new publications that are not present in the database. "
    "Script [`update_database.py`](https://github.com/GMestreM/ragxiv/blob/main/update_database.py) "
    "is responsible for checking if the new articles are already present in the database, "
    "chunking the documents and storing both the content and its embeddings into "
    "the vector database."
)
mdFile.new_paragraph(
    "A `cron-job` is used to automatically run this script at a given schedule, "
    "which ensures that the knowledge base is always up to date."
)

mdFile.new_header(level=2, title="Monitoring")

mdFile.new_paragraph("TO-DO")

mdFile.new_header(level=2, title="Containerization")

mdFile.new_paragraph(
    "A `docker-compose.yaml` file is provided, which eases "
    "the setup stage of the project. The `docker-compose` file "
    "contains both the main application and their dependencies "
    "such as the postgres database (with `pg_vector` already installed). "
    ""
)

mdFile.new_paragraph(
    "[Instruction](https://github.com/GMestreM/ragxiv/tree/main?tab=readme-ov-file#using-docker-compose) are also provided to set up the project using "
    "a simple `docker-compose build`; which starts the postgres database, "
    "initializes it, populates the database with recent documents "
    "and it launches the Streamlit interface so the user can interact with "
    "ragXiv."
)

mdFile.new_header(level=2, title="Reproducibility")

mdFile.new_paragraph(
    "The [setup section](https://github.com/GMestreM/ragxiv/tree/main?tab=readme-ov-file#setup) "
    "of the project README file describes in detail how to set up the project "
    "(specifying all environment variables that have to be included in the `.env` file, "
    "versions for all dependencies are specified in [`requirements.txt`](https://github.com/GMestreM/ragxiv/blob/main/requirements.txt)), run the "
    "application (either locally or using docker-compose)."
)

mdFile.new_paragraph(
    "The dataset that ragXiv uses is free and available at [arXiv](https://arxiv.org/) "
    "and the application contains functions to retrieve documents. However, as per "
    "[arXiv terms of use](https://info.arxiv.org/help/api/tou.html), I cannot "
    "store and serve e-prints from my server, so the only method implemented in ragXiv to "
    "retrieve arXiv documents is to use their API and store the embeddings in the local "
    "postgres database. "
)
mdFile.new_paragraph(
    "   > Store and serve arXiv e-prints (PDFs, source files, or other content) "
    " from your servers, unless you have the permission of the copyright holder "
    " or are permitted to do so by the license with which the e-print was "
    " submitted. Note that a very small subset of arXiv e-prints are submitted "
    " with licenses that permit redistribution."
)

mdFile.new_header(level=2, title="Bonus points - Cloud deployment")

mdFile.new_paragraph(
    "ragXiv has been deployed to the cloud, using [Render Cloud](https://render.com/) "
    "platform and using [Supabase](https://supabase.com/) for the POstgreSQL database used "
    "by the app. [ragXiv can be accessed here](https://ragxiv.onrender.com/) "
)

mdFile.new_paragraph(
    " - Please note that this deployment has been made using both "
    "[Render Cloud](https://render.com/) and [Supabase](https://supabase.com/) "
    "free tiers, so there may be some delay when accessing the app (as it needs to wake up "
    "the container) and it may take some time to process the queries."
)


mdFile.new_table_of_contents(table_title="Contents", depth=2)
mdFile.create_md_file()
