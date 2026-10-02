import json
from pathlib import Path

from ..agent.graph import graph, AgentGraphState


# -------------------------
# Load Evaluation Dataset
# -------------------------

def load_evaluation_dataset():

    project_root = Path(__file__).resolve().parents[2]

    dataset_path = (
        project_root
        / "data"
        / "evaluation"
        / "agent_evaluation.json"
    )

    with open(
        dataset_path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# -------------------------
# Evaluate One Query
# -------------------------

def evaluate_query(item):

    query = item["query"]
    expected_tools = item["expected_tools"]
    expected_tool_calls = item.get("expected_tool_calls", [])

    initial_state: AgentGraphState = {
        "user_query": query,
        "messages": [
            {
                "role": "user",
                "content": query
            }
        ],
        "tool_results": [],
        "final_answer": None,
        "iterations": 0
    }

    result = graph.invoke(initial_state)

    actual_tools = [
        tool["name"]
        for tool in result["tool_results"]
    ]

    actual_tool_calls = result["tool_results"]

    tool_correct = (
        actual_tools == expected_tools
    )

    arguments_correct = True

    if expected_tool_calls:

        for expected_call in expected_tool_calls:

            tool_name = expected_call["name"]
            expected_arguments = expected_call["arguments"]

            matching_calls = [
                call
                for call in actual_tool_calls
                if call["name"] == tool_name
            ]

            if not matching_calls:
                arguments_correct = False
                break

            actual_arguments = matching_calls[0]["arguments"]

            for key, value in expected_arguments.items():

                if actual_arguments.get(key) != value:
                    arguments_correct = False
                    break

            if not arguments_correct:
                break

    return {
        "query": query,
        "expected_tools": expected_tools,
        "actual_tools": actual_tools,
        "tool_correct": tool_correct,
        "arguments_correct": arguments_correct,
        "answer": result["final_answer"]
    }


# -------------------------
# Calculate Metrics
# -------------------------

def calculate_metrics(results):

    total = len(results)

    tool_accuracy = sum(
        result["tool_correct"]
        for result in results
    ) / total

    return {
        "queries": total,
        "tool_accuracy": tool_accuracy
    }


# -------------------------
# Print Report
# -------------------------

def print_report(results, metrics):

    print("\n" + "=" * 60)
    print("Agent Evaluation")
    print("=" * 60)

    for i, result in enumerate(
        results,
        start=1
    ):

        print(f"\nQuery {i}:")
        print(result["query"])

        print(
            f"Expected: "
            f"{', '.join(result['expected_tools'])}"
        )

        print(
            f"Actual:   "
            f"{', '.join(result['actual_tools'])}"
        )

        print(
            f"Correct:  "
            f"{result['tool_correct']}"
        )

        print("\nAnswer:")
        print(result["answer"])

    print("\n" + "-" * 60)
    print("Overall Metrics")
    print("-" * 60)

    print(
        f"Queries       : "
        f"{metrics['queries']}"
    )

    print(
        f"Tool Accuracy : "
        f"{metrics['tool_accuracy']:.3f}"
    )

    print("=" * 60)


# -------------------------
# Main
# -------------------------

def run_evaluation():

    dataset = load_evaluation_dataset()

    results = []

    for item in dataset:

        result = evaluate_query(item)

        results.append(result)

    metrics = calculate_metrics(results)

    print_report(
        results,
        metrics
    )


if __name__ == "__main__":
    run_evaluation()