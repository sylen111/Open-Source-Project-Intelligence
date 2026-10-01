import json

from .rag import (
    get_db_connection,
    retrieve_chunks,
)
from sentence_transformers import SentenceTransformer


EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

TOP_K = 5


def load_questions():

    with open(
        "data/evaluation_questions.json",
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def evaluate():

    model = SentenceTransformer(
        EMBEDDING_MODEL
    )

    conn = get_db_connection()

    questions = load_questions()

    total = len(questions)
    hit_count = 0

    try:

        for item in questions:

            question = item["question"]
            expected_projects = item["expected_projects"]

            results = retrieve_chunks(
                conn,
                question,
                model,
                TOP_K
            )

            retrieved_projects = [
                result[0]
                for result in results
            ]

            hit = any(
                project in retrieved_projects
                for project in expected_projects
            )

            if hit:
                hit_count += 1

            print("\nQuestion:")
            print(question)

            print("Expected:")
            print(expected_projects)

            print("Retrieved:")
            print(retrieved_projects)

            print("Hit:", hit)

        recall_at_k = hit_count / total

        print("\n====================")
        print("Retrieval Evaluation")
        print("====================")

        print(
            f"Recall@{TOP_K}: "
            f"{recall_at_k:.2%}"
        )

    finally:

        conn.close()


if __name__ == "__main__":
    evaluate()