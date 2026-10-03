from typing import Any
from sentence_transformers import SentenceTransformer
from src.db import get_db_connection, get_project_details
from src.rag.rag import retrieve_chunks
from src.ingestion.ingestion import fetch_github_projects

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
RELEVANCE_THRESHOLD = 0.75

def search_rag(query: str) -> dict[str, Any]:
    """
    Search project knowledge using vector and hybrid retrieval.

    Args:
        query: Natural language question or search query.

    Returns:
        Relevant project chunks and metadata.
    """
    conn = get_db_connection()

    try:
        embedding_model = SentenceTransformer(
            EMBEDDING_MODEL
        )

        results = retrieve_chunks(
            conn,
            query,
            embedding_model,
            top_k=5
        )

        formatted_results = []

        for result in results:
            (
                project_name,
                description,
                language,
                stars,
                category,
                use_cases,
                technologies,
                summary,
                content,
                vector_similarity,
                keyword_score,
                hybrid_score,       
            ) = result

            formatted_results.append({
                "project_name": project_name,
                "description": description,
                "language": language,
                "stars": stars,
                "category": category,
                "use_cases": use_cases,
                "technologies": technologies,
                "summary": summary,
                "content": content,
                "vector_similarity": float(vector_similarity),
                "keyword_score": float(keyword_score),
                "hybrid_score": float(hybrid_score),
            })

        relevant_results = [
            result
            for result in formatted_results
            if result["hybrid_score"] >= RELEVANCE_THRESHOLD
        ]

        return {
            "tool": "search_rag",
            "query": query,
            "found": bool(relevant_results),
            "result_count": len(relevant_results),
            "results": relevant_results
        }

    finally:
        conn.close()


def get_project_details_tool(project_name: str) -> dict[str, Any]:
    """
    Get detailed information about a specific project.

    Args:
        project_name: Name or full name of the GitHub project.

    Returns:
        Project details from PostgreSQL.
    """

    result = get_project_details(project_name)

    return {
        "tool": "get_project_details",
        "project_name": project_name,
        "result": result,
    }


def fetch_github_projects_tool(
    query: str,
    sort: str = "stars",
    order: str = "desc",
    max_results: int = 10,
) -> dict[str, Any]:

    if max_results < 1 or max_results > 20:
        raise ValueError("max_results must be between 1 and 20")

    if sort not in {
        "stars",
        "forks",
        "help-wanted-issues",
        "updated",
    }:
        raise ValueError("Invalid sort option")

    if order not in {"asc", "desc"}:
        raise ValueError("order must be 'asc' or 'desc'")

    project_ids = fetch_github_projects(
        query=query,
        total=max_results,
        sort=sort,
        order=order,
    )

    return {
        "tool": "fetch_github_projects",
        "query": query,
        "sort": sort,
        "order": order,
        "fetched": len(project_ids),
        "project_ids": project_ids,
    }

TOOLS = {
    "search_rag": search_rag,
    "get_project_details": get_project_details_tool,
    "fetch_github_projects": fetch_github_projects_tool,
}