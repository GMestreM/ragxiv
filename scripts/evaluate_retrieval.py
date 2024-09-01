import os
import sys
import ast
import pandas as pd
from dotenv import load_dotenv
from typing import TypedDict, List, Final
from tqdm.auto import tqdm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ragxiv.database import (
    open_db_connection,
    PostgresParams,
    SemanticSearch,
)
from ragxiv.retrieval import retrieve_similar_documents

load_dotenv("./.env")

PATH_EVALUATION_QUESTIONS = "metadata_evaluation_questions_725_fixed.csv"

# Default embedding parameters
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
frame_evaluation_filt = frame_evaluation_filt.iloc[:4, :]


# Loop over each article id; for each question
# search for similar documents and check if the
# original document is retrieved
class EvaluationRetrieval(TypedDict):
    original_id: str
    evaluation_question: str
    id_retrieved_documents: List[str]


retrieved_documents = []
for original_id, row in tqdm(
    frame_evaluation_filt.iterrows(), total=frame_evaluation_filt.shape[0]
):
    for question in row:
        semantic_search_abstract = SemanticSearch(
            query=question,
            table=TABLE_EMBEDDING_ABSTRACT,
            similarity_metric="<#>",
            embedding_model=EMBEDDING_MODEL_NAME,
            max_documents=3,
        )

        relevant_documents = retrieve_similar_documents(
            conn=conn,
            retrieval_method=RETRIEVAL_METHOD,
            retrieval_parameters=[semantic_search_abstract, semantic_search_abstract],
        )

        id_retrieved_documents = relevant_documents["references"]

        evaluation = EvaluationRetrieval(
            original_id=original_id,
            evaluation_question=question,
            id_retrieved_documents=id_retrieved_documents,
        )
        retrieved_documents.append(evaluation)


frame_output = pd.DataFrame(retrieved_documents)
frame_output.to_csv(
    f"retrieval_evaluation_results_{frame_output.shape[0]}.csv", sep=";"
)
# pd.read_csv(f'retrieval_evaluation_results_{frame_output.shape[0]}.csv', sep=';', index_col=[0])

# Obtain metrics
