from .fetch_repos import fetch_repositories, save_raw_data
from .pipeline import run_pipeline
from .ingest_readmes import ingest_readmes
from .enrich_projects import enrich_projects
from .create_chunks import create_embeddings


def fetch_github_projects(
    query,
    total=10,
    sort="stars",
    order="desc",
):
    """
    Fetch GitHub projects and process them through
    the complete ingestion pipeline.

    Args:
        query: GitHub repository search query.
        total: Maximum number of repositories to fetch.
        sort: GitHub sorting field.
        order: GitHub sorting order.

    Returns:
        List of PostgreSQL project IDs.
    """

    print(f"Fetching GitHub projects: {query}")
    print(f"Sort: {sort}, Order: {order}")

    # 1. Fetch
    repositories = fetch_repositories(
        query=query,
        total=total,
        sort=sort,
        order=order,
    )

    if not repositories:
        print("No repositories found.")
        return []

    # 2. Save raw data
    filename = save_raw_data(repositories)

    # 3. Transform + validate + load into PostgreSQL
    project_ids = run_pipeline(filename)

    if not project_ids:
        print("No valid projects were loaded.")
        return []

    # 4. Fetch README
    ingest_readmes(project_ids)

    # 5. AI enrichment
    enrich_projects(project_ids)

    # 6. Create chunks + embeddings
    create_embeddings(project_ids)

    print(
        f"Ingestion completed for "
        f"{len(project_ids)} projects."
    )

    return project_ids