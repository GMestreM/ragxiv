import os
import pandas as pd
from mdutils.mdutils import MdUtils

FILE_PATH = os.path.join("reports", "llm_zoomcamp_final_project_report")
RETRIEVAL_PATH = os.path.join("reports", "data", "comparison_retrieval_methods.csv")
RAG_PATH = os.path.join("reports", "data", "comparison_rag_methods.csv")

mdFile = MdUtils(file_name=FILE_PATH, title="LLM Zoomcamp - Final Project report")

mdFile.new_paragraph(
    "ragXiv is my final project for the 2024 edition of the [LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp/). "
    "This report contains the different evaluation criteria for the projects, and illustrates how the project adresses them. "
)

mdFile.new_header(level=1, title="Evaluation criteria")
mdFile.new_header(level=2, title="Problem description")

mdFile.new_paragraph(
    "The problem that ragXiv tried to solve is described in detail at "
    "[the README.md file of this repository](https://github.com/GMestreM/ragxiv?tab=readme-ov-file#problem-statement): "
)

mdFile.new_paragraph(
    "ragXiv is a Retrieval-Augmented Generation (RAG) system developed to enhance "
    "the extraction of information and the communication of expert-level knowledge "
    "in the field of academic quantitative finance. By leveraging the extensive "
    "repository of academic papers available on arXiv, ragXiv streamlines the process "
    "of retrieving, synthesizing, and presenting relevant information from scholarly "
    "literature. This system aims to make complex quantitative finance topics more "
    "accessible to researchers and professionals alike."
)

mdFile.new_paragraph("The problem that it tries to solve can be summarized as: ")
markdown_list = [
    "The rapid expansion of academic literature "
    "as created significant challenges for researchers and professionals. "
    "Staying current with the latest developments is increasingly difficult due to the "
    "overwhelming volume of published papers."
    "",
    "Traditional search engines and academic databases primarily offer keyword-based "
    "search functionalities, which often fail to provide contextually relevant or precise results. "
    "",
    "ragXiv seeks to address these challenges by implementing an advanced two-step "
    "semantic search and retrieval system,  effectively filtering through the "
    "extensive pool of academic papers to identify those most relevant to the user's query. "
    "",
    "It then generates expert-level explanations, ensuring that users receive clear, "
    "concise, and contextually appropriate information tailored to their needs. "
    "",
]
mdFile.new_list(markdown_list)

mdFile.new_header(level=2, title="RAG flow")

mdFile.new_paragraph(
    "The RAG (Retrieval-Augmented Generation) flow in ragXiv is designed to "
    "integrate both a comprehensive knowledge base and a powerful Large Language Model (LLM) "
    "to deliver precise and expert-level responses to user queries. "
    "As stated in the "
    "[project key features](https://github.com/GMestreM/ragxiv?tab=readme-ov-file#key-features), "
    "the different elements employed in the RAG flow are: "
)

markdown_list = [
    " **Knowledge base**: The backbone of the ragXiv system is a knowledge base "
    "consisting of scholarly articles sourced from [arXiv](https://arxiv.org/), "
    "a widely recognized open-access repository for academic papers. "
    "This rich repository serves as the primary source of information, encompassing "
    "a vast array of topics within quantitative finance."
    "",
    " **Vector database**: To facilitate efficient retrieval of relevant documents, "
    "ragXiv employs a vector database powered by PostgreSQL with the "
    "[`pg_vector` extension](https://github.com/pgvector/pgvector). This database not "
    "only stores the vector embeddings of the documents but also plays a critical role "
    "in the semantic search process, retrieving only the most contextually relevant "
    "documents for a given query."
    "",
    " **LLM integration**: After the relevant documents are identified, the extracted "
    "context is fed into a Large Language Model (LLM). The LLM is responsible for "
    "synthesizing the retrieved information and generating responses that are not "
    "only accurate but also clear, concise, and reflective of expert-level "
    "understanding. This combination of precise retrieval and advanced natural "
    "language generation enables ragXiv to effectively bridge the gap between "
    "complex academic literature and the user need for accessible, high-quality insights."
    "",
]
mdFile.new_list(markdown_list)

mdFile.new_header(level=2, title="Retrieval evaluation")

mdFile.new_paragraph(
    "Multiple retrieval methods have been evalutated "
    "(check [script `evaluate_retrieval.py`](https://github.com/GMestreM/ragxiv/blob/main/scripts/evaluate_retrieval.py)). "
    " The evaluation focused on comparing different methods for their ability "
    "to accurately retrieve documents in response to user queries. "
    "The methods assessed are as follows: "
)
markdown_list = [
    "`pg_semantic_abstract+article`: This method employs a two-step semantic search. Initially, "
    " a semantic search is conducted between the user query and the abstracts "
    "of academic papers. This step effectively narrows down the document pool to those "
    "most contextually aligned with the query. In the second step, another semantic search "
    "is performed, this time targeting the body content of the selected papers. "
    "This approach ensures that not only the most relevant documents are selected "
    "but also that the most pertinent sections within those documents are considered."
    "",
    "`pg_semantic_article`: This method performs a single-step semantic search across the body content "
    "of all documents stored in the vector database.  While this approach is effective in "
    "identifying relevant content, it does not benefit from the initial filtering "
    "step that focuses on document abstracts."
    "",
    "`pg_text_article`: This method utilizes a traditional keyword-based text search "
    "across the body content of all documents stored in the vector database. "
    "It relies solely on keyword matching and does not leverage semantic understanding, "
    "which may limit its effectiveness in retrieving contextually relevant information. "
    "",
]
mdFile.new_list(markdown_list)
mdFile.new_paragraph(
    "To compare the effectiveness of these retrieval methods, two key metrics "
    "were used: `hit_rate` and `mean_reciprocal_rank` (MRR)."
    "The hit rate measures the proportion of relevant documents "
    "retrieved by the system, whereas MRR evaluates the rank of the first relevant "
    "document in the search results, with higher values indicating that relevant "
    "documents appear earlier in the results."
)
mdFile.new_paragraph(
    "The table below summarizes the performance of each retrieval method: "
)
retrieval_metrics = pd.read_csv(RETRIEVAL_PATH, sep=";", index_col=[0])
mdFile.new_paragraph(retrieval_metrics.to_markdown())

mdFile.new_paragraph(
    "The best results are obtained with the **`pg_semantic_abstract+article`** "
    "method, so it will be used in the final application."
)

mdFile.new_header(level=2, title="RAG evaluation")

mdFile.new_paragraph(
    "To determine the most effective Retrieval-Augmented Generation (RAG) "
    "approach for ragXiv, I tested three different Large Language Models (LLMs) "
    "to compare their performance: "
)
markdown_list = [
    "`llama3-70b-8192`",
    "`gemma2-9b-it`",
    "`llama-3.1-70b-versatile`",
]
mdFile.new_list(markdown_list)

mdFile.new_paragraph(
    "I employed an LLM-as-a-Judge evaluation criterion, which involves the following steps: "
)
markdown_list = [
    " **Question and Retrieval**: For each user query, the RAG system retrieves relevant "
    "documents from the knowledge base and generates an answer using one of the tested LLMs. "
    "",
    " **Judging Relevance**: After generating the answer, a different LLM is used to evaluate the "
    "relevance of the generated response in relation to the original user query."
    "",
    " **Scoring**: The relevance is scored, and the average relevance score is calculated for each LLM."
    "",
]
mdFile.new_list(markdown_list)

mdFile.new_paragraph(
    "Script `evaluate_rag.py` was used for this task. "
    "The results obtained are summarized in the following table: "
)

rag_metrics = pd.read_csv(RAG_PATH, sep=";", index_col=[0])
mdFile.new_paragraph(rag_metrics.to_markdown())

mdFile.new_paragraph(
    "As shown in the table, the `llama3-70b-8192` model consistently produced "
    "the most relevant answers according to the LLM-as-a-Judge evaluation. Based "
    "on these results, `llama3-70b-8192` has been selected as the preferred LLM model "
    "for the ragXiv RAG system. "
)

mdFile.new_header(level=2, title="Interface")

mdFile.new_paragraph(
    "A user-friendly interface using Streamlit has been developed to facilitate the interaction with "
    "the application.  This interface provides users with an intuitive chat-based platform that simplifies "
    "the process of querying the RAG system and receiving expert-level responses, as "
    "illustrated in [this figure](https://github.com/GMestreM/ragxiv/tree/main?tab=readme-ov-file#overview)."
)

mdFile.new_header(level=2, title="Ingestion pipeline")

mdFile.new_paragraph(
    "ragXiv features an automated ingestion pipeline designed to periodically "
    "update its knowledge base with the latest academic publications. "
    "This pipeline is crucial for ensuring that the system remains current and relevant. "
    "Script [`update_database.py`](https://github.com/GMestreM/ragxiv/blob/main/update_database.py) "
    "is responsible for checking if the new articles are already present in the database, "
    "chunking the documents and storing both the content and its embeddings into "
    "the vector database."
)

mdFile.new_paragraph(
    "By integrating an automated ingestion pipeline with a scheduled `cron-job`, "
    "ragXiv ensures that its knowledge base is always populated with the most recent "
    "and relevant academic papers, enhancing the system's ability to provide "
    "accurate and timely responses. "
)

mdFile.new_header(level=2, title="Monitoring")

mdFile.new_paragraph(
    "The chat interface build with Streamlit asks users for their "
    "feedback using a thumbs up/down system. Our app collects this data "
    "and stores it into the PostgreSQL database, in order to monitor "
    "the satisfaction of our users and improve the service. Specifically, "
    "ragXiv collects: "
)

markdown_list = [
    " **User ID**: A unique identifier for each user session" "",
    " **Question**: The query or issue submitted." "",
    " **Answer**: The response provided by the system." "",
    " **Satisfaction Rating**: Your thumbs-up or thumbs-down rating of the response."
    "",
    " **Documents Retrieved**: Any relevant documents or references provided." "",
    " **Elapsed Time**: The time taken to generate the response." "",
    " **Feedback Timestamp**: The exact time when feedback was provided." "",
]
mdFile.new_list(markdown_list)


mdFile.new_header(level=2, title="Containerization")

mdFile.new_paragraph(
    "To streamline the setup and deployment process, the entire ragXiv project is "
    "fully containerized using Docker, with a comprehensive `docker-compose.yaml` "
    "file provided. This file encapsulates the entire project, including the main "
    "ragXiv application and all necessary dependencies, such as a PostgreSQL "
    "database with the `pg_vector` extension pre-installed, which is essential "
    "for the system's vector-based retrieval functionalities. "
    ""
)

mdFile.new_paragraph(
    "The Docker Compose setup automates the entire workflow. "
    "[As per the instructions](https://github.com/GMestreM/ragxiv/tree/main?tab=readme-ov-file#using-docker-compose), "
    "by running a "
    "simple `docker-compose up --build`, the following steps are executed "
    "automatically: "
    ""
)

markdown_list = [
    "The PostgreSQL database is launched and initialized with the necessary schemas and extensions"
    "",
    "The database is populated with recent academic documents retrieved from arXiv." "",
    "The Streamlit interface is launched, allowing users to interact with ragXiv "
    "immediately upon setup completion. "
    "",
]
mdFile.new_list(markdown_list)

mdFile.new_paragraph(
    "The containerization ensures that the ragXiv project can be deployed consistently "
    "across different environments without the need for manual configuration or dependency "
    "management. This makes the system highly portable and accessible to users with minimal setup effort. "
)

mdFile.new_header(level=2, title="Reproducibility")

mdFile.new_paragraph(
    "The [setup section](https://github.com/GMestreM/ragxiv/tree/main?tab=readme-ov-file#setup) "
    "of the project README file provides comprehensive guidance on how to set up ragXiv, which include "
    "specifying all environment variables that need to be configured in the `.env` file, and managing "
    "the dependencies required for the project, as they are all listed in the "
    "[`requirements.txt`](https://github.com/GMestreM/ragxiv/blob/main/requirements.txt) file, including "
    "version specifications to avoid compatibility issues. Additionally, instructions about how to "
    "run the application are included (either locally or using `docker-compose`). "
)

mdFile.new_paragraph(
    "The dataset used by ragXiv consists of academic papers freely available "
    "through  [arXiv](https://arxiv.org/). While the project cannot store and serve "
    "e-prints directly due to [arXiv terms of use](https://info.arxiv.org/help/api/tou.html), "
    "it includes functions to retrieve documents via the arXiv API. This approach "
    "ensures compliance with arXiv policies while allowing users to populate their local "
    "database with the necessary data. The implemented API-based retrieval system "
    "allows users to fetch recent documents on demand and store them as embeddings in the "
    "local PostgreSQL database."
)
# mdFile.new_paragraph(
#     "   > Store and serve arXiv e-prints (PDFs, source files, or other content) "
#     " from your servers, unless you have the permission of the copyright holder "
#     " or are permitted to do so by the license with which the e-print was "
#     " submitted. Note that a very small subset of arXiv e-prints are submitted "
#     " with licenses that permit redistribution."
# )

mdFile.new_paragraph(
    "The project has been tested to ensure that it works as described, and the "
    "instructions provided are designed to minimize any potential issues during setup or execution"
)

mdFile.new_header(level=2, title="Bonus points - Cloud deployment")

mdFile.new_paragraph(
    "ragXiv has been deployed to the cloud, using [Render Cloud](https://render.com/) "
    "platform and using [Supabase](https://supabase.com/) for the POstgreSQL database used "
    "by the app. This deployment allows users to access ragXiv from anywhere without the "
    "need for local setup. [ragXiv can be accessed from this link](https://ragxiv.onrender.com/) "
)

mdFile.new_paragraph(
    " - **Performance Considerations**: Please note that this deployment uses the free tiers of both "
    "[Render Cloud](https://render.com/) and [Supabase](https://supabase.com/). "
    "As a result, there may be some latency when accessing the app, particularly if the container "
    "needs to be woken up. Additionally, processing queries may take longer than expected due to the "
    "limitations of the free tier resources."
)


mdFile.new_table_of_contents(table_title="Contents", depth=2)
mdFile.create_md_file()
