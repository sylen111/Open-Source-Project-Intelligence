import os
import re
from sentence_transformers import SentenceTransformer
from ..db import get_db_connection

MODEL_NAME = "BAAI/bge-small-en-v1.5"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def clean_text(text):
    # Remove markdown table separator rows
    text = re.sub(
        r"\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?",
        "",
        text
    )

    # Remove markdown links but keep link text
    text = re.sub(
        r"\[([^\]]+)\]\([^)]+\)",
        r"\1",
        text
    )

    # Remove excessive markdown symbols
    text = re.sub(
        r"[|]{2,}",
        " ",
        text
    )

    # Remove excessive whitespace
    text = re.sub(
        r"\n\s*\n\s*\n+",
        "\n\n",
        text
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    return text.strip()


# -------------------------
# Chunking
# -------------------------

def create_chunks(text):
    text = clean_text(text)

    chunks = []

    start = 0
    chunk_index = 0

    while start < len(text):

        end = start + CHUNK_SIZE

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(
                (chunk_index, chunk)
            )

        start = end - CHUNK_OVERLAP
        chunk_index += 1

    return chunks


# -------------------------
# Get README + Enrichment
# -------------------------

def get_project_readmes(conn):

    query = """
        SELECT
            p.id,
            p.name,
            r.content,

            pe.category,
            pe.use_cases,
            pe.technologies,
            pe.summary

        FROM projects p

        JOIN project_readmes r
            ON p.id = r.project_id

        LEFT JOIN project_enrichments pe
            ON p.id = pe.project_id

        ORDER BY p.id;
    """

    with conn.cursor() as cursor:

        cursor.execute(query)

        return cursor.fetchall()


def get_projects_by_ids(conn, project_ids):
    query = """
        SELECT
            p.id,
            p.name,
            r.content,
            pe.category,
            pe.use_cases,
            pe.technologies,
            pe.summary
        FROM projects p
        JOIN project_readmes r
            ON p.id = r.project_id
        LEFT JOIN project_enrichments pe
            ON p.id = pe.project_id
        WHERE p.id = ANY(%s)
        ORDER BY p.id;
    """

    with conn.cursor() as cursor:
        cursor.execute(query, (project_ids,))
        return cursor.fetchall()


# -------------------------
# Build Embedding Text
# -------------------------

def build_embedding_text(
    project_name,
    category,
    use_cases,
    technologies,
    summary,
    content
):

    use_cases_text = ", ".join(
        use_cases or []
    )

    technologies_text = ", ".join(
        technologies or []
    )

    return f"""
Project: {project_name}

Category: {category or ""}

Use cases: {use_cases_text}

Technologies: {technologies_text}

Summary: {summary or ""}

README:
{content}
""".strip()


# -------------------------
# Save Chunks
# -------------------------

def save_chunks(
    conn,
    project_id,
    chunks,
    embeddings
):

    query = """
        INSERT INTO project_chunks (
            project_id,
            chunk_index,
            content,
            embedding
        )
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (project_id, chunk_index)
        DO UPDATE SET
            content = EXCLUDED.content,
            embedding = EXCLUDED.embedding;
    """

    with conn.cursor() as cursor:

        for (chunk_index, content), embedding in zip(
            chunks,
            embeddings
        ):

            cursor.execute(
                query,
                (
                    project_id,
                    chunk_index,
                    content,
                    embedding.tolist(),
                )
            )

    conn.commit()


def create_embeddings(project_ids):
    """
    Create chunks and embeddings for the specified projects.

    Args:
        project_ids: PostgreSQL project IDs to process.
    """
    if not project_ids:
        return

    conn = get_db_connection()

    try:
        projects = get_projects_by_ids(conn, project_ids)

        print(f"Found {len(projects)} projects for embedding.")

        embedding_model = SentenceTransformer(MODEL_NAME)

        for project in projects:
            (
                project_id,
                project_name,
                content,
                category,
                use_cases,
                technologies,
                summary,
            ) = project

            chunks = create_chunks(content)

            if not chunks:
                continue

            embedding_texts = []

            for _, chunk in chunks:
                embedding_texts.append(
                    build_embedding_text(
                        project_name,
                        category,
                        use_cases,
                        technologies,
                        summary,
                        chunk,
                    )
                )

            embeddings = embedding_model.encode(
                embedding_texts,
                normalize_embeddings=True,
            )

            save_chunks(
                conn,
                project_id,
                chunks,
                embeddings,
            )

            print(f"Created embeddings: {project_name}")

    finally:
        conn.close()


def main():

    conn = get_db_connection()

    model = SentenceTransformer(MODEL_NAME)

    try:

        projects = get_project_readmes(conn)

        print(
            f"Projects with README: {len(projects)}"
        )

        for (
            project_id,
            name,
            readme,
            category,
            use_cases,
            technologies,
            summary
        ) in projects:

            print(f"\nProcessing: {name}")

            chunks = create_chunks(readme)

            print(
                f"Chunks created: {len(chunks)}"
            )

            texts = [
                build_embedding_text(
                    name,
                    category,
                    use_cases,
                    technologies,
                    summary,
                    content
                )
                for _, content in chunks
            ]

            embeddings = model.encode(
                texts,
                normalize_embeddings=True
            )

            save_chunks(
                conn,
                project_id,
                chunks,
                embeddings
            )

            print("Saved.")

    finally:

        conn.close()


if __name__ == "__main__":
    main()