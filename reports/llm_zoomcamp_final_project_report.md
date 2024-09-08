
LLM Zoomcamp - Final Project report
===================================

Contents
========

* [Evaluation criteria](#evaluation-criteria)
	* [Problem description](#problem-description)
	* [RAG flow](#rag-flow)
	* [Retrieval evaluation](#retrieval-evaluation)
	* [RAG evaluation](#rag-evaluation)
	* [Interface](#interface)
	* [Ingestion pipeline](#ingestion-pipeline)
	* [Monitoring](#monitoring)
	* [Containerization](#containerization)
	* [Reproducibility](#reproducibility)
	* [Bonus points - Cloud deployment](#bonus-points---cloud-deployment)


ragXiv is my final project for the 2024 edition of the [LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp/). This report contains the different evaluation criteria for the projects, and illustrates how the project adresses them.
# Evaluation criteria

## Problem description


The problem that ragXiv tried to solve is described in detail at [the README.md file of this repository](https://github.com/GMestreM/ragxiv?tab=readme-ov-file#problem-statement):

ragXiv is a Retrieval-Augmented Generation (RAG) system developed to enhance the extraction of information and the communication of expert-level knowledge in the field of academic quantitative finance. By leveraging the extensive repository of academic papers available on arXiv, ragXiv streamlines the process of retrieving, synthesizing, and presenting relevant information from scholarly literature. This system aims to make complex quantitative finance topics more accessible to researchers and professionals alike.

The problem that it tries to solve can be summarized as:
- The rapid expansion of academic literature as created significant challenges for researchers and professionals. Staying current with the latest developments is increasingly difficult due to the overwhelming volume of published papers.
- Traditional search engines and academic databases primarily offer keyword-based search functionalities, which often fail to provide contextually relevant or precise results.
- ragXiv seeks to address these challenges by implementing an advanced two-step semantic search and retrieval system,  effectively filtering through the extensive pool of academic papers to identify those most relevant to the user's query.
- It then generates expert-level explanations, ensuring that users receive clear, concise, and contextually appropriate information tailored to their needs.

## RAG flow


The RAG (Retrieval-Augmented Generation) flow in ragXiv is designed to integrate both a comprehensive knowledge base and a powerful Large Language Model (LLM) to deliver precise and expert-level responses to user queries. As stated in the [project key features](https://github.com/GMestreM/ragxiv?tab=readme-ov-file#key-features), the different elements employed in the RAG flow are:
-  **Knowledge base**: The backbone of the ragXiv system is a knowledge base consisting of scholarly articles sourced from [arXiv](https://arxiv.org/), a widely recognized open-access repository for academic papers. This rich repository serves as the primary source of information, encompassing a vast array of topics within quantitative finance.
-  **Vector database**: To facilitate efficient retrieval of relevant documents, ragXiv employs a vector database powered by PostgreSQL with the [`pg_vector` extension](https://github.com/pgvector/pgvector). This database not only stores the vector embeddings of the documents but also plays a critical role in the semantic search process, retrieving only the most contextually relevant documents for a given query.
-  **LLM integration**: After the relevant documents are identified, the extracted context is fed into a Large Language Model (LLM). The LLM is responsible for synthesizing the retrieved information and generating responses that are not only accurate but also clear, concise, and reflective of expert-level understanding. This combination of precise retrieval and advanced natural language generation enables ragXiv to effectively bridge the gap between complex academic literature and the user need for accessible, high-quality insights.

## Retrieval evaluation


Multiple retrieval methods have been evalutated (check [script `evaluate_retrieval.py`](https://github.com/GMestreM/ragxiv/blob/main/scripts/evaluate_retrieval.py)).  The evaluation focused on comparing different methods for their ability to accurately retrieve documents in response to user queries. The methods assessed are as follows:
- `pg_semantic_abstract+article`: This method employs a two-step semantic search. Initially,  a semantic search is conducted between the user query and the abstracts of academic papers. This step effectively narrows down the document pool to those most contextually aligned with the query. In the second step, another semantic search is performed, this time targeting the body content of the selected papers. This approach ensures that not only the most relevant documents are selected but also that the most pertinent sections within those documents are considered.
- `pg_semantic_article`: This method performs a single-step semantic search across the body content of all documents stored in the vector database.  While this approach is effective in identifying relevant content, it does not benefit from the initial filtering step that focuses on document abstracts.
- `pg_text_article`: This method utilizes a traditional keyword-based text search across the body content of all documents stored in the vector database. It relies solely on keyword matching and does not leverage semantic understanding, which may limit its effectiveness in retrieving contextually relevant information.


To compare the effectiveness of these retrieval methods, two key metrics were used: `hit_rate` and `mean_reciprocal_rank` (MRR).The hit rate measures the proportion of relevant documents retrieved by the system, whereas MRR evaluates the rank of the first relevant document in the search results, with higher values indicating that relevant documents appear earlier in the results.

The table below summarizes the performance of each retrieval method:

|                      |   pg_semantic_abstract+article |   pg_semantic_article |   pg_text_article |
|:---------------------|-------------------------------:|----------------------:|------------------:|
| hit_rate             |                       0.91     |              0.858333 |          0.576667 |
| mean_reciprocal_rank |                       0.867639 |              0.811667 |          0.4825   |

The best results are obtained with the **`pg_semantic_abstract+article`** method, so it will be used in the final application.
## RAG evaluation


To determine the most effective Retrieval-Augmented Generation (RAG) approach for ragXiv, I tested three different Large Language Models (LLMs) to compare their performance:
- `llama3-70b-8192`
- `gemma2-9b-it`
- `llama-3.1-70b-versatile`


I employed an LLM-as-a-Judge evaluation criterion, which involves the following steps:
-  **Question and Retrieval**: For each user query, the RAG system retrieves relevant documents from the knowledge base and generates an answer using one of the tested LLMs.
-  **Judging Relevance**: After generating the answer, a different LLM is used to evaluate the relevance of the generated response in relation to the original user query.
-  **Scoring**: The relevance is scored, and the average relevance score is calculated for each LLM.


Script `evaluate_rag.py` was used for this task. The results obtained are summarized in the following table:

|                 |   llama3-70b-8192 |   gemma2-9b-it |   llama-3.1-70b-versatile |
|:----------------|------------------:|---------------:|--------------------------:|
| RELEVANT        |        0.956667   |      0.493333  |                 0.903333  |
| PARTLY_RELEVANT |        0.0366667  |      0.413333  |                 0.0966667 |
| NON_RELEVANT    |        0.00666667 |      0.0933333 |               nan         |

As shown in the table, the `llama3-70b-8192` model consistently produced the most relevant answers according to the LLM-as-a-Judge evaluation. Based on these results, `llama3-70b-8192` has been selected as the preferred LLM model for the ragXiv RAG system.
## Interface


A user-friendly interface using Streamlit has been developed to facilitate the interaction with the application.  This interface provides users with an intuitive chat-based platform that simplifies the process of querying the RAG system and receiving expert-level responses, as illustrated in [this figure](https://github.com/GMestreM/ragxiv/tree/main?tab=readme-ov-file#overview).
## Ingestion pipeline


ragXiv features an automated ingestion pipeline designed to periodically update its knowledge base with the latest academic publications. This pipeline is crucial for ensuring that the system remains current and relevant. Script [`update_database.py`](https://github.com/GMestreM/ragxiv/blob/main/update_database.py) is responsible for checking if the new articles are already present in the database, chunking the documents and storing both the content and its embeddings into the vector database.

By integrating an automated ingestion pipeline with a scheduled `cron-job`, ragXiv ensures that its knowledge base is always populated with the most recent and relevant academic papers, enhancing the system's ability to provide accurate and timely responses.
## Monitoring


The chat interface build with Streamlit asks users for their feedback using a thumbs up/down system. Our app collects this data and stores it into the PostgreSQL database, in order to monitor the satisfaction of our users and improve the service. Specifically, ragXiv collects:
-  **User ID**: A unique identifier for each user session
-  **Question**: The query or issue submitted.
-  **Answer**: The response provided by the system.
-  **Satisfaction Rating**: Your thumbs-up or thumbs-down rating of the response.
-  **Documents Retrieved**: Any relevant documents or references provided.
-  **Elapsed Time**: The time taken to generate the response.
-  **Feedback Timestamp**: The exact time when feedback was provided.


File `streamlit_feedback_monitor.py` defines a Streamlit dashboard used to monitor user feedback using different charts. Currently these 5 charts are being used:
-  `User Ratings Distribution`: A bar chart visualizing the count of thumbs up, thumbs down, and no rating values.
-  `Feedback Over Time`: A line chart showing the number of feedback entries over time, grouped by date.
-  `Average Response Time`: A line chart showing the average elapsed time (in seconds) for generating responses, grouped by date.
-  `Top Retrieved Documents`: A bar chart displaying the top 10 most frequently retrieved documents.
-  `Frequent User Queries`: A bar chart showing the 10 most common words found in user queries.

## Containerization


To streamline the setup and deployment process, the entire ragXiv project is fully containerized using Docker, with a comprehensive `docker-compose.yaml` file provided. This file encapsulates the entire project, including the main ragXiv application and all necessary dependencies, such as a PostgreSQL database with the `pg_vector` extension pre-installed, which is essential for the system's vector-based retrieval functionalities.

The Docker Compose setup automates the entire workflow. [As per the instructions](https://github.com/GMestreM/ragxiv/tree/main?tab=readme-ov-file#using-docker-compose), by running a simple `docker-compose up --build`, the following steps are executed automatically:
- The PostgreSQL database is launched and initialized with the necessary schemas and extensions
- The database is populated with recent academic documents retrieved from arXiv.
- The Streamlit interface is launched, allowing users to interact with ragXiv immediately upon setup completion.


The containerization ensures that the ragXiv project can be deployed consistently across different environments without the need for manual configuration or dependency management. This makes the system highly portable and accessible to users with minimal setup effort.
## Reproducibility


The [setup section](https://github.com/GMestreM/ragxiv/tree/main?tab=readme-ov-file#setup) of the project README file provides comprehensive guidance on how to set up ragXiv, which include specifying all environment variables that need to be configured in the `.env` file, and managing the dependencies required for the project, as they are all listed in the [`requirements.txt`](https://github.com/GMestreM/ragxiv/blob/main/requirements.txt) file, including version specifications to avoid compatibility issues. Additionally, instructions about how to run the application are included (either locally or using `docker-compose`).

The dataset used by ragXiv consists of academic papers freely available through  [arXiv](https://arxiv.org/). While the project cannot store and serve e-prints directly due to [arXiv terms of use](https://info.arxiv.org/help/api/tou.html), it includes functions to retrieve documents via the arXiv API. This approach ensures compliance with arXiv policies while allowing users to populate their local database with the necessary data. The implemented API-based retrieval system allows users to fetch recent documents on demand and store them as embeddings in the local PostgreSQL database.

The project has been tested to ensure that it works as described, and the instructions provided are designed to minimize any potential issues during setup or execution
## Bonus points - Cloud deployment


ragXiv has been deployed to the cloud, using [Render Cloud](https://render.com/) platform and using [Supabase](https://supabase.com/) for the POstgreSQL database used by the app. This deployment allows users to access ragXiv from anywhere without the need for local setup. [ragXiv can be accessed from this link](https://ragxiv.onrender.com/)

 - **Performance Considerations**: Please note that this deployment uses the free tiers of both [Render Cloud](https://render.com/) and [Supabase](https://supabase.com/). As a result, there may be some latency when accessing the app, particularly if the container needs to be woken up. Additionally, processing queries may take longer than expected due to the limitations of the free tier resources.
