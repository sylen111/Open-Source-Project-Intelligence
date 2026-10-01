from datetime import datetime
from ..db import get_db_connection


def insert_projects(repositories):
    conn = get_db_connection()
    cursor = conn.cursor()

    project_ids = []

    project_query = """
        INSERT INTO projects (
            github_id, name, full_name, owner, description,
            html_url, homepage, language, stars, forks, open_issues,
            size, is_fork, archived, license, default_branch,
            created_at, updated_at, pushed_at, fetched_at
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        )
        ON CONFLICT (github_id)
        DO UPDATE SET
            stars = EXCLUDED.stars,
            forks = EXCLUDED.forks,
            open_issues = EXCLUDED.open_issues,
            size = EXCLUDED.size,
            archived = EXCLUDED.archived,
            updated_at = EXCLUDED.updated_at,
            pushed_at = EXCLUDED.pushed_at,
            fetched_at = EXCLUDED.fetched_at
        RETURNING id;
    """

    topic_query = """
        INSERT INTO topics (name)
        VALUES (%s)
        ON CONFLICT (name)
        DO UPDATE SET name = EXCLUDED.name
        RETURNING id;
    """

    relation_query = """
        INSERT INTO project_topics (project_id, topic_id)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING;
    """

    try:
        for repo in repositories:
            cursor.execute(
                project_query,
                (
                    repo["github_id"],
                    repo["name"],
                    repo["full_name"],
                    repo["owner"],
                    repo["description"],
                    repo["html_url"],
                    repo["homepage"],
                    repo["language"],
                    repo["stars"],
                    repo["forks"],
                    repo["open_issues"],
                    repo["size"],
                    repo["is_fork"],
                    repo["archived"],
                    repo["license"],
                    repo["default_branch"],
                    repo["created_at"],
                    repo["updated_at"],
                    repo["pushed_at"],
                    datetime.now(),
                ),
            )

            project_id = cursor.fetchone()[0]
            project_ids.append(project_id)

            for topic_name in repo["topics"]:
                cursor.execute(topic_query, (topic_name,))
                topic_id = cursor.fetchone()[0]

                cursor.execute(
                    relation_query,
                    (project_id, topic_id),
                )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()

    print(f"Loaded {len(project_ids)} repositories.")

    return project_ids

