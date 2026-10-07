import json
from pydantic import BaseModel, Field
from ..db import get_db_connection
from ..agent.llm import create_llm_client

llm_client = create_llm_client()

# -------------------------
# Structured Output Schema
# -------------------------

class ProjectEnrichment(BaseModel):
    category: str = Field(
        description="Main category of the GitHub project"
    )

    use_cases: list[str] = Field(
        min_length=1,
        description="Main practical use cases of the project"
    )

    technologies: list[str] = Field(
        min_length=1,
        description="Main technologies, frameworks, or tools used"
    )

    summary: str = Field(
        min_length=1,
        description="Short summary explaining what the project does"
    )


# -------------------------
# Get Projects
# -------------------------

def get_projects_without_enrichment(conn):
    query = """
        SELECT
            p.id,
            p.name,
            p.description,
            p.language,
            p.html_url,
            r.content AS readme
        FROM projects p
        LEFT JOIN project_readmes r
            ON p.id = r.project_id
        LEFT JOIN project_enrichments pe
            ON p.id = pe.project_id
        WHERE pe.project_id IS NULL
        ORDER BY p.stars DESC;
    """

    with conn.cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()

def get_projects_by_ids(conn, project_ids):
    query = """
        SELECT
            p.id,
            p.name,
            p.description,
            p.language,
            p.html_url,
            r.content AS readme
        FROM projects p
        LEFT JOIN project_readmes r
            ON p.id = r.project_id
        WHERE p.id = ANY(%s);
    """

    with conn.cursor() as cursor:
        cursor.execute(query, (project_ids,))
        return cursor.fetchall()

# -------------------------
# AI Enrichment
# -------------------------

def enrich_project(project):
    project_id, name, description, language, html_url, readme = project

    prompt = f"""
You are analyzing a GitHub open-source project.

Project name:
{name}

Description:
{description}

Primary language:
{language}

GitHub URL:
{html_url}

README:
{readme}

Analyze the project using all the information above.

Rules:
- category must be short and specific
- use_cases must contain practical use cases
- technologies must contain important technologies, frameworks, or tools
- summary should briefly explain what the project does
- prioritize information supported by the README
- do not invent information
- return only the requested structured output
"""

    result = llm_client.structured_output(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        schema=ProjectEnrichment,
    )

    return result


def enrich_projects(project_ids):
    """
    Generate AI enrichment for the specified projects.

    Args:
        project_ids: PostgreSQL project IDs to enrich.
    """
    if not project_ids:
        return

    conn = get_db_connection()

    try:
        projects = get_projects_by_ids(conn, project_ids)

        print(f"Found {len(projects)} projects for enrichment.")

        for project in projects:
            try:
                enrichment = enrich_project(project)

                save_enrichment(
                    conn,
                    project[0],
                    enrichment,
                )

                print(f"Enriched project: {project[1]}")

            except Exception as e:
                print(
                    f"Failed to enrich "
                    f"{project[1]}: {e}"
                )

    finally:
        conn.close()


# -------------------------
# Save Enrichment
# -------------------------

def save_enrichment(conn, project_id, enrichment):
    query = """
        INSERT INTO project_enrichments (
            project_id,
            category,
            use_cases,
            technologies,
            summary,
            model
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (project_id)
        DO UPDATE SET
            category = EXCLUDED.category,
            use_cases = EXCLUDED.use_cases,
            technologies = EXCLUDED.technologies,
            summary = EXCLUDED.summary,
            model = EXCLUDED.model,
            enriched_at = CURRENT_TIMESTAMP;
    """

    with conn.cursor() as cursor:
        cursor.execute(
            query,
            (
                project_id,
                enrichment.category,
                json.dumps(enrichment.use_cases),
                json.dumps(enrichment.technologies),
                enrichment.summary,
                llm_client.model,
            ),
        )

    conn.commit()


# -------------------------
# Main
# -------------------------

def main():

    conn = get_db_connection()

    try:
        projects = get_projects_without_enrichment(conn)

        print(f"Projects to enrich: {len(projects)}")

        for project in projects:

            project_id = project[0]
            project_name = project[1]

            print(f"\nEnriching: {project_name}")

            try:
                enrichment = enrich_project(project)

                print("Category:", enrichment.category)
                print("Use cases:", enrichment.use_cases)
                print("Technologies:", enrichment.technologies)
                print("Summary:", enrichment.summary)

                save_enrichment(
                    conn,
                    project_id,
                    enrichment
                )

                print("Saved.")

            except Exception as e:
                print(f"Failed: {e}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()