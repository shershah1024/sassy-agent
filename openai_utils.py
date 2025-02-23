#never edit this file
from typing import Type, TypeVar
from pydantic import BaseModel
import os
from openai import AsyncAzureOpenAI

T = TypeVar('T', bound=BaseModel)

async def structured_openai_completion(
    instructions: str,
    original_content: str,
    response_model: Type[T], 
    max_tokens: int = 2000, 
    temperature: float = 0.7
) -> T:
    openai_client = AsyncAzureOpenAI(
        azure_endpoint=os.getenv("azure_text_endpoint"),
        api_key=os.getenv("azure_text_api_key"),
        api_version=os.getenv("azure_text_api_version"),
    )

    print(f"instructions: {instructions}")
    print(f"original_content: {original_content}")
    print(f"response_model: {response_model}")

    structured_completion = await openai_client.beta.chat.completions.parse(
        model="gpt-4o-3",
        messages=[
            {
                "role": "system",
                "content": f"{instructions}+ please use the structure given"
            },
            {
                "role": "user",
                "content": original_content
            }
        ],
        response_format=response_model,
        temperature=temperature,
        max_tokens=max_tokens
    )
    print(f"structured_completion: {structured_completion}")

    structured_response = structured_completion.choices[0].message.parsed
    
    # Print token usage
    input_tokens = structured_completion.usage.prompt_tokens
    output_tokens = structured_completion.usage.completion_tokens
    print(f"GPT-4 - Input tokens: {input_tokens}, Output tokens: {output_tokens}")

    return structured_response

