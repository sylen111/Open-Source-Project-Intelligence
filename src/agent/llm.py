import os
import json
import ollama
from typing import Any, TypeVar
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
T = TypeVar("T", bound=BaseModel)

class ToolCall(BaseModel):
    id: str | None = None
    name: str
    arguments: dict[str, Any]

class LLMClient:
    model: str
    
    def chat(
        self,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        raise NotImplementedError

    def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        raise NotImplementedError

    def structured_output(
        self,
        messages: list[dict[str, Any]],
        schema: type[T],
    ) -> T:
        raise NotImplementedError


class OllamaClient(LLMClient):

    def __init__(self):
        host = os.getenv(
            "OLLAMA_HOST",
            "http://localhost:11434"
        )

        self.client = ollama.Client(host=host)
        self.model = "qwen2.5:3b"

    def chat(
        self,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:

        response = self.client.chat(
            model=self.model,
            messages=messages,
        )

        return {
            "content": response["message"]["content"]
        }

    def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:

        response = self.client.chat(
            model=self.model,
            messages=messages,
            tools=tools,
        )

        message = response["message"]

        tool_calls = []

        for tool_call in message.get("tool_calls") or []:

            tool_calls.append(
                ToolCall(
                    id=None,
                    name=tool_call.function.name,
                    arguments=tool_call.function.arguments,
                ).model_dump()
            )

        return {
            "content": message.get("content"),
            "tool_calls": tool_calls,
        }

    def structured_output(
        self,
        messages: list[dict[str, Any]],
        schema: type[T],
    ) -> T:

        response = self.client.chat(
            model=self.model,
            messages=messages,
            format=schema.model_json_schema(),
        )

        content = response["message"]["content"]

        return schema.model_validate_json(content)


class OpenAIClient(LLMClient):

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set"
            )

        self.client = OpenAI(api_key=api_key)

        self.model = os.getenv(
            "OPENAI_MODEL",
            "gpt-6-luna"
        )

        self.previous_response_id = None

    def chat(
        self,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:

        response = self.client.responses.create(
            model=self.model,
            input=messages,
        )

        return {
            "content": response.output_text
        }

    def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:

        openai_tools = []

        for tool in tools:
            function = tool["function"]

            openai_tools.append(
                {
                    "type": "function",
                    "name": function["name"],
                    "description": function["description"],
                    "parameters": function["parameters"],
                }
            )

        if self.previous_response_id is None:

            # First request:
            # send the normal conversation to OpenAI.
            input_messages = messages

            response = self.client.responses.create(
                model=self.model,
                input=input_messages,
                tools=openai_tools,
            )

        else:

            # Subsequent requests:
            # the previous response already contains the
            # assistant's function_call.
            #
            # We only need to send the tool outputs.
            input_messages = []

            for message in messages:

                if message.get("role") != "tool":
                    continue

                input_messages.append(
                    {
                        "type": "function_call_output",
                        "call_id": message["tool_call_id"],
                        "output": message["content"],
                    }
                )

            response = self.client.responses.create(
                model=self.model,
                input=input_messages,
                tools=openai_tools,
                previous_response_id=self.previous_response_id,
            )

        self.previous_response_id = response.id

        tool_calls = []

        for item in response.output:

            if item.type != "function_call":
                continue

            tool_calls.append(
                ToolCall(
                    id=item.call_id,
                    name=item.name,
                    arguments=json.loads(item.arguments),
                ).model_dump()
            )

        return {
            "content": response.output_text,
            "tool_calls": tool_calls,
        }

    def structured_output(
        self,
        messages: list[dict[str, Any]],
        schema: type[T],
    ) -> T:

        schema_json = schema.model_json_schema()

        schema_json["additionalProperties"] = False

        response = self.client.responses.create(
            model=self.model,
            input=messages,
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema.__name__,
                    "schema": schema_json,
                    "strict": True,
                }
            },
        )

        return schema.model_validate_json(
            response.output_text
        )
        

def create_llm_client() -> LLMClient:
    provider = os.getenv(
        "LLM_PROVIDER",
        "ollama"
    ).lower()

    if provider == "ollama":
        return OllamaClient()

    if provider == "openai":
        return OpenAIClient()

    raise ValueError(
        f"Unsupported LLM provider: {provider}"
    )