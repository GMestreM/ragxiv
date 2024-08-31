import os
import sys
import time
import json
import pandas as pd
from dotenv import load_dotenv
from tqdm.auto import tqdm
from typing import Final, TypedDict, List


class EvaluationQuestions(TypedDict):
    document_id: str
    questions: List[str]


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ragxiv.llm import (
    llm_chat_completion,
    GroqParams,
    build_retrieval_evaluation_prompt,
)

load_dotenv("./.env")

METADATA_PATH = "metadata_all.csv"
MARKDOWN_ARTICLES_PATH = "article_markdown.csv"

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
LLM_MODEL: Final = "groq"
LLM_MODEL_PARAMS = GroqParams(api_key=GROQ_API_KEY, model="llama-3.1-70b-versatile")

# Load documents
metadata = pd.read_csv(METADATA_PATH, sep=";")
markdown_text = pd.read_csv(MARKDOWN_ARTICLES_PATH, sep=";")
# Filter metadata by id
metadata = metadata.loc[metadata["id"].isin(markdown_text["id"]), :]
metadata.set_index("id", inplace=True)

# Loop and build questions
eval_questions = []
failed_to_parse = []

for idx, row in tqdm(metadata.iterrows(), total=metadata.shape[0]):
    time.sleep(2)
    document_id = row["entry_url"]
    abstract = row["summary"]

    query = build_retrieval_evaluation_prompt(document=abstract, number_questions=3)

    response = llm_chat_completion(
        query=query, llm_model=LLM_MODEL, llm_parameters=LLM_MODEL_PARAMS
    )
    # print(response["response"])

    # Parse response into lists
    try:
        questions = json.loads(response["response"])
    except Exception as e:
        print(document_id)
        failed_to_parse.append(document_id)
        questions = response["response"]
    eval_question = EvaluationQuestions(document_id=document_id, questions=questions)
    eval_questions.append(eval_question)

# Store as csv file
print(failed_to_parse)
pd.DataFrame(eval_questions).to_csv(
    f"metadata_evaluation_questions_{metadata.shape[0]}.csv", sep=";"
)

# len(pd.DataFrame(eval_questions).iloc[0,:]['questions']) == 3

# Read file:
# test = pd.read_csv(f"metadata_evaluation_questions_{metadata.shape[0]}.csv", sep=';', index_col=[0])
# import ast
# test['questions'] = test['questions'].apply(ast.literal_eval)
# len(test.iloc[0,:]['questions']) == 3
