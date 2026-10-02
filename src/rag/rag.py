import os
import re
import ollama
from sentence_transformers import SentenceTransformer
from ..db import get_db_connection


EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
LLM_MODEL = "qwen2.5:3b"

TOP_K = 5

STOPWORDS = {
    "which",
    "projects",
    "project",
    "are",
    "is",
    "the",
    "a",
    "an",
    "for",
    "to",
    "of",
    "in",
    "on",
    "and",
    "or",
    "with",
    "related",
    "allow",
    "allows",
    "user",
    "users",
    "build",
    "built",
}


# -------------------------
# Retrieval
# -------------------------

def retrieve_chunks(
    conn,
    query,
    embedding_model,
    top_k=TOP_K
):
    query_embedding = embedding_model.encode(
        query,
        normalize_embeddings=True
    )

    keywords = extract_keywords(query)

    if not keywords:
        keywords = [query.lower()]

    keyword_conditions = []

    params = [
        query_embedding.tolist()
    ]

    for keyword in keywords:

        pattern = f"%{keyword}%"

        keyword_conditions.append(
            """
            CASE
                WHEN
                    pe.summary ILIKE %s
                    OR pe.use_cases::text ILIKE %s
                    OR pe.technologies::text ILIKE %s
                    OR p.description ILIKE %s
                    OR pc.content ILIKE %s
                THEN 1
                ELSE 0
            END
            """
        )

        params.extend([
            pattern,
            pattern,
            pattern,
            pattern,
            pattern,
        ])

    keyword_score_sql = " + ".join(
        keyword_conditions
    )

    sql = f"""
        SELECT
            *,
            (
                0.7 * vector_similarity
                +
                0.3 * keyword_score
            ) AS hybrid_score

        FROM (
            SELECT DISTINCT ON (p.id)

                p.name,
                p.description,
                p.language,
                p.stars,

                pe.category,
                pe.use_cases,
                pe.technologies,
                pe.summary,

                pc.content,

                1 - (pc.embedding <=> %s::vector)
                    AS vector_similarity,

                ({keyword_score_sql})::float
                    / {len(keywords)}
                    AS keyword_score

            FROM project_chunks pc

            JOIN projects p
                ON p.id = pc.project_id

            LEFT JOIN project_enrichments pe
                ON pe.project_id = p.id

            ORDER BY
                p.id,
                pc.embedding <=> %s::vector

        ) AS project_results

        ORDER BY hybrid_score DESC

        LIMIT %s;
    """

    params.append(
        query_embedding.tolist()
    )

    params.append(top_k)

    with conn.cursor() as cursor:

        cursor.execute(
            sql,
            tuple(params)
        )

        return cursor.fetchall()
    
# -------------------------
# Build Context
# -------------------------

def build_context(results):

    context_parts = []

    for i, result in enumerate(
        results,
        start=1
    ):

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

        context_parts.append(
            f"""
SOURCE {i}

Project:
{project_name}

Description:
{description}

Language:
{language}

Stars:
{stars}

Category:
{category}

Use cases:
{use_cases}

Technologies:
{technologies}

AI Summary:
{summary}

README:
{content}

Vector similarity:
{vector_similarity:.4f}

Keyword score:
{keyword_score:.4f}

Hybrid score:
{hybrid_score:.4f}
"""
        )

    return "\n".join(context_parts)

# -------------------------
# Generate Answer
# -------------------------

def generate_answer(query, context):

    prompt = f"""
You are an assistant that answers questions about
open-source AI and LLM projects.

Use ONLY the provided context.

If the answer cannot be found in the context,
say that the information is not available.

Context:

{context}

Question:

{query}

Answer clearly and concisely.
"""

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    return response["message"]["content"]

def extract_keywords(query):

    words = re.findall(
        r"\b[a-zA-Z0-9-]+\b",
        query.lower()
    )

    keywords = [
        word
        for word in words
        if word not in STOPWORDS
        and len(word) > 2
    ]

    return keywords

# -------------------------
# Main RAG Pipeline
# -------------------------

def main():

    query = input("Question: ")

    conn = get_db_connection()

    embedding_model = SentenceTransformer(
        EMBEDDING_MODEL
    )

    try:

        # 1. Retrieve
        results = retrieve_chunks(
            conn,
            query,
            embedding_model
        )

        # 2. Build context
        context = build_context(results)

        # 3. Generate answer
        answer = generate_answer(
            query,
            context
        )

        print("\nAnswer:")
        print(answer)

        print("\nRetrieved sources:")

        for result in results:
            project_name = result[0]
            vector_similarity = result[9]
            keyword_score = result[10]
            hybrid_score = result[11]

            print(
                f"- {project_name} "
                f"(vector={vector_similarity:.4f}, "
                f"keyword={keyword_score:.4f}, "
                f"hybrid={hybrid_score:.4f})"
            )

    finally:

        conn.close()


if __name__ == "__main__":
    main()