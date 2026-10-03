import os
from typing import Any

import psycopg2
from dotenv import load_dotenv


load_dotenv()


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def get_project_details(
    project_name: str,
) -> dict[str, Any] | None:

    conn = get_db_connection()

    try:
        sql = """
            SELECT
                p.id,
                p.github_id,
                p.name,
                p.full_name,
                p.owner,
                p.description,
                p.html_url,
                p.homepage,
                p.language,
                p.stars,
                p.forks,
                p.open_issues,
                p.size,
                p.is_fork,
                p.archived,
                p.license,
                p.default_branch,
                p.created_at,
                p.updated_at,
                p.pushed_at,
                pe.category,
                pe.use_cases,
                pe.technologies,
                pe.summary,
                pr.content AS readme
            FROM projects p

            LEFT JOIN project_enrichments pe
                ON pe.project_id = p.id

            LEFT JOIN project_readmes pr
                ON pr.project_id = p.id

            WHERE
                LOWER(p.name) = LOWER(%s)
                OR LOWER(p.full_name) = LOWER(%s)

            LIMIT 1;
        """

        with conn.cursor() as cursor:
            cursor.execute(
                sql,
                (project_name, project_name)
            )

            row = cursor.fetchone()

        if row is None:
            return None

        (
            project_id,
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
            category,
            use_cases,
            technologies,
            summary,
            readme,
        ) = row

        return {
            "project_id": project_id,
            "github_id": github_id,
            "name": name,
            "full_name": full_name,
            "owner": owner,
            "description": description,
            "html_url": html_url,
            "homepage": homepage,
            "language": language,
            "stars": stars,
            "forks": forks,
            "open_issues": open_issues,
            "size": size,
            "is_fork": is_fork,
            "archived": archived,
            "license": license,
            "default_branch": default_branch,
            "created_at": created_at,
            "updated_at": updated_at,
            "pushed_at": pushed_at,
            "category": category,
            "use_cases": use_cases,
            "technologies": technologies,
            "summary": summary,
            "readme": readme,
        }

    finally:
        conn.close()