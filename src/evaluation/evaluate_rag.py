import json
from pathlib import Path

from sentence_transformers import SentenceTransformer

from ..db import get_db_connection
from ..rag.rag import (
    retrieve_chunks,
    EMBEDDING_MODEL,
)


TOP_K = 5


# -------------------------
# Load Evaluation Dataset
# -------------------------

def load_evaluation_dataset():

    project_root = Path(__file__).resolve().parents[2]

    dataset_path = (
        project_root
        / "data"
        / "evaluation"
        / "rag_evaluation.json"
    )

    with open(dataset_path, "r", encoding="utf-8") as file:
        return json.load(file)


# -------------------------
# Evaluate One Query
# -------------------------

def evaluate_query(
    conn,
    embedding_model,
    item
):

    query = item["query"]
    expected_projects = {
        project.lower()
        for project in item["expected_projects"]
    }

    results = retrieve_chunks(
        conn,
        query,
        embedding_model,
        top_k=TOP_K
    )

    retrieved_projects = [
        result[0]
        for result in results
    ]

    retrieved_projects_lower = [
        project.lower()
        for project in retrieved_projects
    ]

    # -------------------------
    # Hit@K
    # -------------------------

    hit_at_1 = int(
        any(
            project in expected_projects
            for project in retrieved_projects_lower[:1]
        )
    )

    hit_at_3 = int(
        any(
            project in expected_projects
            for project in retrieved_projects_lower[:3]
        )
    )

    hit_at_5 = int(
        any(
            project in expected_projects
            for project in retrieved_projects_lower[:5]
        )
    )

    # -------------------------
    # Reciprocal Rank
    # -------------------------

    reciprocal_rank = 0.0

    for rank, project in enumerate(
        retrieved_projects_lower,
        start=1
    ):

        if project in expected_projects:
            reciprocal_rank = 1 / rank
            break

    return {
        "query": query,
        "expected_projects": item["expected_projects"],
        "retrieved_projects": retrieved_projects,
        "hit_at_1": hit_at_1,
        "hit_at_3": hit_at_3,
        "hit_at_5": hit_at_5,
        "reciprocal_rank": reciprocal_rank,
    }


# -------------------------
# Calculate Overall Metrics
# -------------------------

def calculate_metrics(results):

    total = len(results)

    hit_at_1 = sum(
        result["hit_at_1"]
        for result in results
    ) / total

    hit_at_3 = sum(
        result["hit_at_3"]
        for result in results
    ) / total

    hit_at_5 = sum(
        result["hit_at_5"]
        for result in results
    ) / total

    mrr = sum(
        result["reciprocal_rank"]
        for result in results
    ) / total

    return {
        "queries": total,
        "hit_at_1": hit_at_1,
        "hit_at_3": hit_at_3,
        "hit_at_5": hit_at_5,
        "mrr": mrr,
    }


# -------------------------
# Print Report
# -------------------------

def print_report(results, metrics):

    print("\n" + "=" * 60)
    print("RAG Evaluation")
    print("=" * 60)

    for i, result in enumerate(
        results,
        start=1
    ):

        print(f"\nQuery {i}:")
        print(result["query"])

        print(
            f"Expected: "
            f"{', '.join(result['expected_projects'])}"
        )

        print(
            f"Retrieved: "
            f"{', '.join(result['retrieved_projects'])}"
        )

        print(
            f"Hit@1={result['hit_at_1']} | "
            f"Hit@3={result['hit_at_3']} | "
            f"Hit@5={result['hit_at_5']} | "
            f"RR={result['reciprocal_rank']:.3f}"
        )

    print("\n" + "-" * 60)
    print("Overall Metrics")
    print("-" * 60)

    print(f"Queries : {metrics['queries']}")
    print(f"Hit@1   : {metrics['hit_at_1']:.3f}")
    print(f"Hit@3   : {metrics['hit_at_3']:.3f}")
    print(f"Hit@5   : {metrics['hit_at_5']:.3f}")
    print(f"MRR     : {metrics['mrr']:.3f}")

    print("=" * 60)


# -------------------------
# Main
# -------------------------

def run_evaluation():

    dataset = load_evaluation_dataset()

    embedding_model = SentenceTransformer(
        EMBEDDING_MODEL
    )

    conn = get_db_connection()

    try:

        results = []

        for item in dataset:

            result = evaluate_query(
                conn,
                embedding_model,
                item
            )

            results.append(result)

        metrics = calculate_metrics(
            results
        )

        print_report(
            results,
            metrics
        )

    finally:

        conn.close()


if __name__ == "__main__":
    run_evaluation()