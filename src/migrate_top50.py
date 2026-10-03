import psycopg2
from psycopg2.extras import Json


LOCAL_DB = {
    "host": "127.0.0.1",
    "port": 5432,
    "dbname": "ai_project_db",
    "user": "postgres",
    "password": "123456",
}

DOCKER_DB = {
    "host": "127.0.0.1",
    "port": 5434,
    "dbname": "ai_project_db",
    "user": "postgres",
    "password": "123456",
}


def migrate():
    source = psycopg2.connect(**LOCAL_DB)
    target = psycopg2.connect(**DOCKER_DB)

    try:
        source_cur = source.cursor()
        target_cur = target.cursor()

        # 1. Get Top 50 projects
        source_cur.execute("""
            SELECT *
            FROM projects
            ORDER BY stars DESC
            LIMIT 50;
        """)

        projects = source_cur.fetchall()

        source_columns = [desc[0] for desc in source_cur.description]

        print(f"Found {len(projects)} projects.")

        for row in projects:
            project = dict(zip(source_columns, row))

            # 2. Insert project
            target_cur.execute("""
                INSERT INTO projects (
                    github_id,
                    name,
                    full_name,
                    owner,
                    description,
                    html_url,
                    homepage,
                    language,
                    stars,
                    forks,
                    open_issues,
                    size,
                    is_fork,
                    archived,
                    license,
                    default_branch,
                    created_at,
                    updated_at,
                    pushed_at,
                    fetched_at
                )
                VALUES (
                    %(github_id)s,
                    %(name)s,
                    %(full_name)s,
                    %(owner)s,
                    %(description)s,
                    %(html_url)s,
                    %(homepage)s,
                    %(language)s,
                    %(stars)s,
                    %(forks)s,
                    %(open_issues)s,
                    %(size)s,
                    %(is_fork)s,
                    %(archived)s,
                    %(license)s,
                    %(default_branch)s,
                    %(created_at)s,
                    %(updated_at)s,
                    %(pushed_at)s,
                    %(fetched_at)s
                )
                ON CONFLICT (github_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    stars = EXCLUDED.stars,
                    forks = EXCLUDED.forks,
                    updated_at = EXCLUDED.updated_at,
                    pushed_at = EXCLUDED.pushed_at,
                    fetched_at = EXCLUDED.fetched_at
                RETURNING id;
            """, project)

            target_project_id = target_cur.fetchone()[0]
            source_project_id = project["id"]

            # 3. Topics
            source_cur.execute("""
                SELECT t.name
                FROM topics t
                JOIN project_topics pt
                    ON pt.topic_id = t.id
                WHERE pt.project_id = %s;
            """, (source_project_id,))

            topics = source_cur.fetchall()

            for (topic_name,) in topics:
                target_cur.execute("""
                    INSERT INTO topics (name)
                    VALUES (%s)
                    ON CONFLICT (name) DO UPDATE
                    SET name = EXCLUDED.name
                    RETURNING id;
                """, (topic_name,))

                target_topic_id = target_cur.fetchone()[0]

                target_cur.execute("""
                    INSERT INTO project_topics (
                        project_id,
                        topic_id
                    )
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING;
                """, (target_project_id, target_topic_id))

            # 4. Enrichment
            source_cur.execute("""
                SELECT
                    category,
                    use_cases,
                    technologies,
                    model,
                    enriched_at,
                    summary
                FROM project_enrichments
                WHERE project_id = %s;
            """, (source_project_id,))

            enrichment = source_cur.fetchone()

            if enrichment:
                (
                    category,
                    use_cases,
                    technologies,
                    model,
                    enriched_at,
                    summary,
                ) = enrichment

                target_cur.execute("""
                    INSERT INTO project_enrichments (
                        project_id,
                        category,
                        use_cases,
                        technologies,
                        model,
                        enriched_at,
                        summary
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (project_id) DO UPDATE SET
                        category = EXCLUDED.category,
                        use_cases = EXCLUDED.use_cases,
                        technologies = EXCLUDED.technologies,
                        model = EXCLUDED.model,
                        enriched_at = EXCLUDED.enriched_at,
                        summary = EXCLUDED.summary;
                """, (
                    target_project_id,
                    category,
                    Json(use_cases),
                    Json(technologies),
                    model,
                    enriched_at,
                    summary,
                ))

            # 5. README
            source_cur.execute("""
                SELECT content, fetched_at
                FROM project_readmes
                WHERE project_id = %s;
            """, (source_project_id,))

            readme = source_cur.fetchone()

            if readme:
                content, fetched_at = readme

                target_cur.execute("""
                    INSERT INTO project_readmes (
                        project_id,
                        content,
                        fetched_at
                    )
                    VALUES (%s, %s, %s)
                    ON CONFLICT (project_id) DO UPDATE SET
                        content = EXCLUDED.content,
                        fetched_at = EXCLUDED.fetched_at;
                """, (
                    target_project_id,
                    content,
                    fetched_at,
                ))

            # 6. Chunks + embeddings
            source_cur.execute("""
                SELECT
                    chunk_index,
                    content,
                    embedding,
                    created_at
                FROM project_chunks
                WHERE project_id = %s
                ORDER BY chunk_index;
            """, (source_project_id,))

            chunks = source_cur.fetchall()

            for chunk_index, content, embedding, created_at in chunks:
                target_cur.execute("""
                    INSERT INTO project_chunks (
                        project_id,
                        chunk_index,
                        content,
                        embedding,
                        created_at
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (project_id, chunk_index) DO UPDATE SET
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        created_at = EXCLUDED.created_at;
                """, (
                    target_project_id,
                    chunk_index,
                    content,
                    embedding,
                    created_at,
                ))

            print(
                f"Migrated: {project['name']} "
                f"({project['stars']} stars)"
            )

        target.commit()

        print("\nMigration completed successfully.")

    except Exception:
        target.rollback()
        raise

    finally:
        source.close()
        target.close()


if __name__ == "__main__":
    migrate()