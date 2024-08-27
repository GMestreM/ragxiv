"""Define LLM functionality by connecting to an external API"""

import os
from typing import Literal, TypedDict, Union
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
