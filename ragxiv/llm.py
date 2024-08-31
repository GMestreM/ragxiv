"""Define LLM functionality by connecting to an external API"""

import os
from typing import Literal, TypedDict, Union, List
from groq import Groq


class GroqParams(TypedDict):
    api_key: str
    model: Literal["llama-3.1-70b-versatile"]


LLM = Literal["groq"]
LLMParameters = Union[GroqParams]


class LLMResponse(TypedDict):
    response: str
    model: str


def llm_chat_completion(
    query: str, llm_model: LLM, llm_parameters: LLMParameters
) -> LLMResponse:
    if llm_model == "groq":
        llm_response = groq_chat_completion(query=query, llm_parameters=llm_parameters)
    else:
        raise ValueError(f"LLM model {llm_model} not implemented")
    return llm_response


def groq_chat_completion(query: str, llm_parameters: GroqParams) -> LLMResponse:
    client = Groq(api_key=llm_parameters["api_key"])

    response = client.chat.completions.create(
        model=llm_parameters["model"],
        messages=[{"role": "user", "content": query}],
    )

    llm_response = LLMResponse(
        response=response.choices[0].message.content,
        model=f"groq  -  {llm_parameters['model']}",
    )
    return llm_response


def build_rag_prompt(user_question: str, context: List[str]) -> str:
    document_string = " \n\n ".join([f"{ document} " for document in context])
    prompt = f"""
    You are an expert in quantitative finance. Answer QUESTION but limit your information to what is inside CONTEXT.

    QUESTION: {user_question}

    CONTEXT: {document_string}
    """
    return prompt


def build_retrieval_evaluation_prompt(document: str, number_questions: int) -> str:
    prompt = f"""
    You are an expert in quantitative finance. Formulate {number_questions}
    questions that you would ask based on an academic paper document. The
    questions should be complete and not too short. If possible, use as
    fewer words as possible from the document.

    The document: {document}


    Provide the output in parsable JSON without using code blocks:
    ["question 1", "question 2", ..., ]
    """
    return prompt
