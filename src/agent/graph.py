import ollama
from typing import Any, TypedDict

from langgraph.graph import StateGraph, START, END

from .agent_config import AGENT_SYSTEM_PROMPT
from .tool_definitions import TOOL_DEFINITIONS
from .agent_tools import TOOLS


MODEL = "qwen2.5:3b"
MAX_ITERATIONS = 5


class AgentGraphState(TypedDict):
    user_query: str
    messages: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]
    final_answer: str | None
    iterations: int


def agent_node(state: AgentGraphState):

    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": AGENT_SYSTEM_PROMPT
            },
            *state["messages"]
        ],
        tools=TOOL_DEFINITIONS
    )

    message = response["message"]

    if not message.get("tool_calls"):
        return {
            "messages": [message],
            "final_answer": message["content"],
            "iterations": state["iterations"] + 1,
        }

    return {
        "messages": [message],
        "iterations": state["iterations"] + 1,
    }


def tools_node(state: AgentGraphState):

    messages = []
    tool_results = []

    last_message = state["messages"][-1]

    for tool_call in last_message["tool_calls"]:

        function_name = tool_call["function"]["name"]
        arguments = tool_call["function"]["arguments"]

        function = TOOLS.get(function_name)

        if function is None:
            raise ValueError(
                f"Unknown tool: {function_name}"
            )

        try:
            result = function(**arguments)

        except Exception as e:
            result = {
                "error": str(e)
            }

        messages.append({
            "role": "tool",
            "content": str(result)
        })

        tool_results.append({
            "name": function_name,
            "result": result
        })

    return {
        "messages": messages,
        "tool_results": tool_results
    }


def should_continue(state: AgentGraphState):

    if state["iterations"] >= MAX_ITERATIONS:
        return "end"

    last_message = state["messages"][-1]

    if last_message.get("tool_calls"):
        return "tools"

    return "end"


graph_builder = StateGraph(AgentGraphState)

graph_builder.add_node("agent", agent_node)
graph_builder.add_node("tools", tools_node)

graph_builder.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "end": END,
    }
)

graph_builder.add_edge(START, "agent")
graph_builder.add_edge("tools", "agent")

graph = graph_builder.compile()


if __name__ == "__main__":

    question = "Tell me about AutoGPT"

    initial_state: AgentGraphState = {
        "user_query": question,
        "messages": [
            {
                "role": "user",
                "content": question
            }
        ],
        "tool_results": [],
        "final_answer": None,
        "iterations": 0
    }

    result = graph.invoke(initial_state)

    print("\nFinal message:")
    print(result["final_answer"])