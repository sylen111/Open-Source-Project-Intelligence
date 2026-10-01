from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-small-en-v1.5"
from ..db import get_db_connection


def search_similar_chunks(conn, query, top_k=5):

    model = SentenceTransformer(MODEL_NAME)

    query_embedding = model.encode(
        query,
        normalize_embeddings=True
    )

    sql = """
        SELECT
            pc.id,
            p.name,
            pc.chunk_index,
            pc.content,
            1 - (pc.embedding <=> %s::vector) AS similarity
        FROM project_chunks pc
        JOIN projects p
            ON p.id = pc.project_id
        ORDER BY pc.embedding <=> %s::vector
        LIMIT %s;
    """

    with conn.cursor() as cursor:

        cursor.execute(
            sql,
            (
                query_embedding.tolist(),
                query_embedding.tolist(),
                top_k,
            )
        )

        return cursor.fetchall()


def main():

    query = input("Question: ")

    conn = get_db_connection()

    try:

        results = search_similar_chunks(
            conn,
            query,
            top_k=5
        )

        print("\nRetrieved chunks:\n")

        for result in results:

            (
                chunk_id,
                project_name,
                chunk_index,
                content,
                similarity
            ) = result

            print("=" * 80)

            print(
                f"Project: {project_name}"
            )

            print(
                f"Chunk: {chunk_index}"
            )

            print(
                f"Similarity: {similarity:.4f}"
            )

            print("\n", content[:1000])

    finally:

        conn.close()


if __name__ == "__main__":
    main()