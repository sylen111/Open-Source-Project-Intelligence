import base64
import logging
import os
import time
import re
import requests
from ..db import get_db_connection

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28",
}

MAX_RETRIES = 3
RETRY_DELAY = 2


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)


def get_projects_without_readme(conn):
    query = """
        SELECT
            p.id,
            p.owner,
            p.name
        FROM projects p
        LEFT JOIN project_readmes r
            ON p.id = r.project_id
        WHERE r.project_id IS NULL
        ORDER BY p.stars DESC;
    """

    with conn.cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()
    

def get_projects_by_ids(conn, project_ids):
    query = """
        SELECT id, owner, name
        FROM projects
        WHERE id = ANY(%s);
    """

    with conn.cursor() as cursor:
        cursor.execute(query, (project_ids,))
        return cursor.fetchall()
    

def clean_readme_text(text):
    """
    Lightly normalize README Markdown for downstream RAG.
    Preserve useful content such as headings, code, and link text.
    """

    # Normalize line endings
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    text = re.sub(
        r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$",
        "",
        text,
        flags=re.MULTILINE
    )

    text = re.sub(
        r"\[([^\]]+)\]\([^)]+\)",
        r"\1",
        text
    )

    text = re.sub(
        r"\|{2,}",
        " ",
        text
    )

    text = re.sub(
        r"[ \t]+$",
        "",
        text,
        flags=re.MULTILINE
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()

def fetch_readme(owner, repo_name):

    url = f"https://api.github.com/repos/{owner}/{repo_name}/readme"

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=15
            )

            if response.status_code == 404:
                logger.warning(
                    f"README not found: {owner}/{repo_name}"
                )
                return None

            if response.status_code == 403:
                logger.warning(
                    "GitHub rate limit or permission issue"
                )
                return None

            response.raise_for_status()

            data = response.json()

            encoded_content = data.get("content")

            if not encoded_content:
                logger.warning(
                    f"README content empty: {owner}/{repo_name}"
                )
                return None

            content = base64.b64decode(
                encoded_content
            ).decode(
                "utf-8",
                errors="replace"
            )

            content = clean_readme_text(content)

            return content

        except requests.RequestException as e:

            logger.warning(
                f"Attempt {attempt} failed for "
                f"{owner}/{repo_name}: {e}"
            )

            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

    logger.error(
        f"Failed to fetch README: "
        f"{owner}/{repo_name}"
    )

    return None


def save_readme(conn, project_id, content):

    query = """
        INSERT INTO project_readmes (
            project_id,
            content
        )
        VALUES (%s, %s)

        ON CONFLICT (project_id)
        DO UPDATE SET
            content = EXCLUDED.content,
            fetched_at = CURRENT_TIMESTAMP;
    """

    with conn.cursor() as cursor:
        cursor.execute(
            query,
            (
                project_id,
                content
            )
        )

    conn.commit()


def ingest_readmes(project_ids):
    """
    Fetch and save README files for the specified projects.

    Args:
        project_ids: PostgreSQL project IDs to process.
    """
    if not project_ids:
        return

    conn = get_db_connection()

    try:
        projects = get_projects_by_ids(conn, project_ids)

        print(f"Found {len(projects)} projects for README ingestion.")

        for project_id, owner, name in projects:
            print(f"Fetching README: {owner}/{name}")

            content = fetch_readme(owner, name)

            if content:
                save_readme(conn, project_id, content)

    finally:
        conn.close()


def main():

    conn = get_db_connection()

    success_count = 0
    failed_count = 0

    try:

        projects = get_projects_without_readme(conn)

        logger.info(
            f"Projects without README: {len(projects)}"
        )

        for project in projects:

            project_id, owner, repo_name = project

            logger.info(
                f"Fetching README: "
                f"{owner}/{repo_name}"
            )

            content = fetch_readme(
                owner,
                repo_name
            )

            if content is None:

                failed_count += 1
                continue

            try:

                save_readme(
                    conn,
                    project_id,
                    content
                )

                success_count += 1

            except Exception as e:

                conn.rollback()

                failed_count += 1

                logger.error(
                    f"Database save failed for "
                    f"{owner}/{repo_name}: {e}"
                )

        logger.info(
            f"README ingestion finished. "
            f"Success={success_count}, "
            f"Failed={failed_count}"
        )

    finally:
        conn.close()


if __name__ == "__main__":
    main()