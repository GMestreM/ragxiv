"""Showcase how obtain retrieval evaluation metrics for a given retrieval configuration"""

import os
import sys
import ast
import pandas as pd
from dotenv import load_dotenv, dotenv_values
from typing import TypedDict, List, Final
from tqdm.auto import tqdm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ragxiv.database import (
    open_db_connection,
    PostgresParams,
    SemanticSearch,
    TextSearch,
)
from ragxiv.retrieval import retrieve_similar_documents

# load_dotenv("./local_env")
environment = dotenv_values("./local_env")

PATH_EVALUATION_QUESTIONS = "metadata_evaluation_questions_725_fixed.csv"

# Default embedding parameters
EMBEDDING_MODEL_NAME: Final = "multi-qa-mpnet-base-dot-v1"

TABLE_EMBEDDING_ARTICLE = f"embedding_article_{EMBEDDING_MODEL_NAME}".replace("-", "_")
TABLE_EMBEDDING_ABSTRACT = f"embedding_abstract_{EMBEDDING_MODEL_NAME}".replace(
    "-", "_"
)

POSTGRES_USER = environment["POSTGRES_USER"]
POSTGRES_PWD = environment["POSTGRES_PWD"]
POSTGRES_DB = environment["POSTGRES_DB"]
POSTGRES_HOST = environment["POSTGRES_HOST"]
POSTGRES_PORT = environment["POSTGRES_PORT"]

RETRIEVAL_METHOD: Final = "pg_semantic_abstract+article"

# Load LLM-generated questions for each id
evaluation_questions = pd.read_csv(PATH_EVALUATION_QUESTIONS, index_col=[0], sep=";")


# Fix and parse each row
list_article_id = []
list_questions = []
for idx, row in evaluation_questions.iterrows():
    article_id = row["document_id"]
    raw_questions = row["questions"]
    try:
        questions = ast.literal_eval(
            raw_questions.replace('"["', '["').replace('"]"', '"]')
        )
    except Exception as e:
        # print(idx, e)
        questions = ast.literal_eval(
            raw_questions.replace('"["', '["').replace("[", '["').replace('"]"', '"]')
        )

    if len(questions) != 3:
        print(idx)

    list_article_id.append(article_id)
    list_questions.append(questions)

dict_evaluation = {}
for i in range(len(list_article_id)):
    dict_evaluation[list_article_id[i]] = list_questions[i]

frame_evaluation = pd.DataFrame.from_dict(dict_evaluation, orient="index")

# Open connection to database
postgres_connection_params = PostgresParams(
    host=POSTGRES_HOST,
    port=POSTGRES_PORT,
    user=POSTGRES_USER,
    pwd=POSTGRES_PWD,
    database=POSTGRES_DB,
)

conn = open_db_connection(connection_params=postgres_connection_params, autocommit=True)

# Get article_id's from database
if conn is not None:
    cur = conn.cursor()
    cur.execute(f"SELECT article_id FROM {TABLE_EMBEDDING_ABSTRACT}")
    document_ids = cur.fetchall()
    document_ids = [doc_id[0] for doc_id in document_ids]
    cur.close()

# Filter evaluation questions using article_id from database
frame_evaluation_filt = frame_evaluation.loc[document_ids, :]

# hit_rate = (number queries that retrieved the relevant document at the top k searches) / total queries
# mean_reciprocal_rank = (1/ total_queries) * (sum (1/rank))


# Loop over each retrieval method
class EvaluationRetrieval(TypedDict):
    original_id: str
    evaluation_question: str
    id_retrieved_documents: List[str]
    hit_rate: bool
    mean_reciprocal_rank: float


RETRIEVAL_METHOD_LIST = [
    "pg_semantic_abstract+article",
    "pg_semantic_article",
    "pg_text_article",
]

final_metrics = {}
for retrieval_method in RETRIEVAL_METHOD_LIST:

    # Check if file has already been obtained
    try:
        frame_output = pd.read_csv(
            f"retrieval_evaluation_results_1200_{retrieval_method}.csv",
            sep=";",
            index_col=[0],
        )
        print(f"{retrieval_method} already obtained")
    except Exception as e:
        print(e)
        # Loop over each article id; for each question
        # search for similar documents and check if the
        # original document is retrieved
        retrieved_documents = []
        for original_id, row in tqdm(
            frame_evaluation_filt.iterrows(), total=frame_evaluation_filt.shape[0]
        ):
            for question in row:
                if retrieval_method == "pg_semantic_abstract+article":
                    semantic_search_abstract = SemanticSearch(
                        query=question,
                        table=TABLE_EMBEDDING_ABSTRACT,
                        similarity_metric="<#>",
                        embedding_model=EMBEDDING_MODEL_NAME,
                        max_documents=3,
                    )
                    retrieval_parameters = [
                        semantic_search_abstract,
                        semantic_search_abstract,
                    ]
                elif retrieval_method == "pg_semantic_article":
                    semantic_search_article = SemanticSearch(
                        query=question,
                        table=TABLE_EMBEDDING_ARTICLE,
                        similarity_metric="<#>",
                        embedding_model=EMBEDDING_MODEL_NAME,
                        max_documents=3,
                    )
                    retrieval_parameters = [semantic_search_article]
                elif retrieval_method == "pg_text_article":
                    text_search_article = SemanticSearch(
                        query=question,
                        table=TABLE_EMBEDDING_ARTICLE,
                        similarity_metric="<#>",
                        embedding_model=EMBEDDING_MODEL_NAME,
                        max_documents=3,
                    )
                    retrieval_parameters = [text_search_article]

                relevant_documents = retrieve_similar_documents(
                    conn=conn,
                    retrieval_method=retrieval_method,
                    retrieval_parameters=retrieval_parameters,
                )

                id_retrieved_documents = relevant_documents["references"]

                # Hit rate
                hit_rate_row = original_id in id_retrieved_documents

                # Mean-reciprocal rank
                try:
                    position = id_retrieved_documents.index(original_id)
                    mean_reciprocal_rank_row = 1 / (position + 1)
                except ValueError:
                    mean_reciprocal_rank_row = 0

                evaluation = EvaluationRetrieval(
                    original_id=original_id,
                    evaluation_question=question,
                    id_retrieved_documents=id_retrieved_documents,
                    hit_rate=hit_rate_row,
                    mean_reciprocal_rank=mean_reciprocal_rank_row,
                )
                retrieved_documents.append(evaluation)

        frame_output = pd.DataFrame(retrieved_documents)
        frame_output.to_csv(
            f"retrieval_evaluation_results_{frame_output.shape[0]}_{retrieval_method}.csv",
            sep=";",
        )

    # # Obtain summary metrics
    # evaluation_metrics = pd.read_csv(
    #     f"retrieval_evaluation_results_1200.csv", sep=";", index_col=[0]
    # )
    # evaluation_metrics["hit_rate"].mean()  # 0.91
    # evaluation_metrics["mean_reciprocal_rank"].mean()  # 0.87

    # Append to dict
    final_metrics[retrieval_method] = {
        "hit_rate": frame_output["hit_rate"].mean(),
        "mean_reciprocal_rank": frame_output["mean_reciprocal_rank"].mean(),
    }
print(final_metrics)
pd.DataFrame(final_metrics).to_csv(
    f"comparison_retrieval_methods_{frame_evaluation_filt.shape[0]}.csv", sep=";"
)
