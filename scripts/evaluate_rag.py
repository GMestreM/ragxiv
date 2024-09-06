import os
import sys
import ast
import time
from dotenv import dotenv_values
import pandas as pd
from typing import Final, cast
from tqdm.auto import tqdm
import json


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ragxiv.database import (
    open_db_connection,
    PostgresParams,
    SemanticSearch,
)
from ragxiv.retrieval import retrieve_similar_documents
from ragxiv.llm import llm_chat_completion, GroqParams, build_rag_prompt, GroqModels

environment = dotenv_values("./local_env")

PATH_EVALUATION_QUESTIONS = "metadata_evaluation_questions_725_fixed.csv"

POSTGRES_USER = environment["POSTGRES_USER"]
POSTGRES_PWD = environment["POSTGRES_PWD"]
POSTGRES_DB = environment["POSTGRES_DB"]
POSTGRES_HOST = environment["POSTGRES_HOST"]
POSTGRES_PORT = environment["POSTGRES_PORT"]

GROQ_API_KEY = environment["GROQ_API_KEY"]

# Default embedding parameters
EMBEDDING_MODEL_NAME: Final = "multi-qa-mpnet-base-dot-v1"

TABLE_EMBEDDING_ARTICLE = f"embedding_article_{EMBEDDING_MODEL_NAME}".replace("-", "_")
TABLE_EMBEDDING_ABSTRACT = f"embedding_abstract_{EMBEDDING_MODEL_NAME}".replace(
    "-", "_"
)

RETRIEVAL_METHOD: Final = "pg_semantic_abstract+article"


def get_rag_evaluation_prompt(question: str, answer_llm: str) -> str:
    rag_evaluation_prompt = f"""
    You are an expert evaluator for a RAG system.
    Your task is to analyze the relevance of the generated answer to the given question.
    Based on the relevance of the generated answer, you will classify it
    as "NON_RELEVANT", "PARTLY_RELEVANT", or "RELEVANT".

    Here is the data for evaluation:

    Question: {question}
    Generated Answer: {answer_llm}

    Please analyze the content and context of the generated answer in relation to the question
    and provide your evaluation in parsable JSON without using code blocks:

    {{
    "Relevance": "NON_RELEVANT" | "PARTLY_RELEVANT" | "RELEVANT",
    "Explanation": "[Provide a brief explanation for your evaluation]"
    }}
    """.strip()

    return rag_evaluation_prompt


# Read evaluation questions
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


# Get a sample of questions
frame_evaluation_filt = frame_evaluation_filt.sample(n=100, random_state=42)


llm_models_test = [
    "llama3-70b-8192",
    "gemma2-9b-it",
    "llama-3.1-70b-versatile",
]

LLM_JUDGE_MODEL_PARAMS = GroqParams(
    api_key=GROQ_API_KEY, model="llama3-groq-70b-8192-tool-use-preview"
)  #

final_metrics = {}

for llm_model in llm_models_test:
    llm_model = cast(GroqModels, llm_model)
    LLM_MODEL_PARAMS = GroqParams(api_key=GROQ_API_KEY, model=llm_model)
    relevance = []
    for original_id, row in tqdm(
        frame_evaluation_filt.iterrows(), total=frame_evaluation_filt.shape[0]
    ):
        for question in row:
            time.sleep(3.1)
            # Use RAG flow
            # Search and retrieve relevant document
            semantic_search_abstract = SemanticSearch(
                query=question,
                table=TABLE_EMBEDDING_ABSTRACT,
                similarity_metric="<#>",
                embedding_model=EMBEDDING_MODEL_NAME,
                max_documents=3,
            )

            semantic_search_article = SemanticSearch(
                query=question,
                table=TABLE_EMBEDDING_ARTICLE,
                similarity_metric="<#>",
                embedding_model=EMBEDDING_MODEL_NAME,
                max_documents=3,
            )

            semantic_search_hierarchy = [
                semantic_search_abstract,
                semantic_search_article,
            ]

            relevant_documents = retrieve_similar_documents(
                conn=conn,
                retrieval_method=RETRIEVAL_METHOD,
                retrieval_parameters=semantic_search_hierarchy,
            )

            # Get answer
            answer_prompt = build_rag_prompt(
                user_question=question, context=relevant_documents["documents"]
            )
            try:
                response = llm_chat_completion(
                    query=answer_prompt,
                    llm_model="groq",
                    llm_parameters=LLM_MODEL_PARAMS,
                )

                # LLM-as-a-judge
                judge_prompt = get_rag_evaluation_prompt(
                    question=question, answer_llm=response["response"]
                )

                time.sleep(3)

                judge_response = llm_chat_completion(
                    query=judge_prompt,
                    llm_model="groq",
                    llm_parameters=LLM_JUDGE_MODEL_PARAMS,
                )
            except Exception as e:
                print(e, original_id)
                response = dict(response="", model="")
                judge_response = dict(response="", model="")

            try:
                dict_judge = json.loads(judge_response["response"])
            except Exception as e:
                print(e, original_id)
                dict_judge = dict(Relevance="", Explanation="")

            dict_append = dict(
                original_id=original_id,
                question=question,
                llm_answer=response["response"],
                judge_answer=judge_response["response"],
                relevance=dict_judge["Relevance"],
                explanation=dict_judge["Explanation"],
            )
            relevance.append(dict_append)

    frame_output = pd.DataFrame(relevance)
    frame_output.to_csv(
        f"rag_evaluation_results_{frame_evaluation_filt.shape[0]}_{llm_model}.csv",
        sep=";",
    )

    final_metrics[llm_model] = (
        frame_output["relevance"].value_counts(normalize=True).to_dict()
    )

print(final_metrics)
pd.DataFrame(final_metrics).to_csv(
    f"comparison_rag_methods_{frame_evaluation_filt.shape[0]}.csv", sep=";"
)
