import json
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from src.ingestion.fetch_repos import (
    fetch_repositories,
    save_raw_data,
    filter_new_or_changed_repositories,
)

from src.ingestion.pipeline import (
    load_raw_data,
    transform_data as run_transform,
)

from src.ingestion.transform_repos import (
    validate_repositories,
    remove_duplicate_repositories,
)

from src.ingestion.load_projects import insert_projects

from src.ingestion.ingest_readmes import ingest_readmes


def fetch_github():
    print("Fetching GitHub repositories...")

    repositories = fetch_repositories(
        query="topic:artificial-intelligence",
        total=10,
        sort="stars",
        order="desc",
    )

    if not repositories:
        raise ValueError("No repositories fetched from GitHub.")

    output_file = save_raw_data(repositories)

    print(f"Raw data saved to: {output_file}")

    return output_file


def incremental_filter(ti):
    input_file = ti.xcom_pull(
        task_ids="fetch_github"
    )

    print(f"Reading raw data from: {input_file}")

    with open(input_file, "r", encoding="utf-8") as f:
        repositories = json.load(f)

    print(f"Fetched repositories: {len(repositories)}")

    filtered = filter_new_or_changed_repositories(
        repositories
    )

    print(
        f"New/changed repositories: {len(filtered)}"
    )

    output_file = save_raw_data(filtered)

    print(f"Filtered data saved to: {output_file}")

    return output_file

def transform(ti):
    input_file = ti.xcom_pull(
        task_ids="incremental_filter"
    )

    print(f"Reading filtered data from: {input_file}")

    raw_data = load_raw_data(input_file)

    print(f"Loaded {len(raw_data)} repositories.")

    transformed = run_transform(raw_data)

    print(f"Transformed {len(transformed)} repositories.")

    return transformed

def validate(ti):
    repositories = ti.xcom_pull(
        task_ids="transform"
    )

    print(
        f"Validating {len(repositories)} repositories..."
    )

    valid, invalid = validate_repositories(
        repositories
    )

    print(f"Valid repositories: {len(valid)}")
    print(f"Invalid repositories: {len(invalid)}")

    if invalid:
        print("\nData Quality Issues:")

        for item in invalid:
            repo = item["repo"]
            errors = item["errors"]

            print(
                f"- {repo.get('github_id')}: "
                f"{', '.join(errors)}"
            )

    if not valid:
        raise ValueError(
            "No valid repositories after validation."
        )

    unique = remove_duplicate_repositories(
        valid
    )

    duplicates_removed = (
        len(valid) - len(unique)
    )

    print(
        f"Duplicates removed: "
        f"{duplicates_removed}"
    )

    print(
        f"Final repositories for loading: "
        f"{len(unique)}"
    )

    return unique


def load(ti):
    repositories = ti.xcom_pull(
        task_ids="validate"
    )

    print(
        f"Loading {len(repositories)} "
        "repositories into PostgreSQL..."
    )

    project_ids = insert_projects(
        repositories
    )

    if not project_ids:
        raise ValueError(
            "No project IDs returned from PostgreSQL."
        )

    print(
        f"Loaded project IDs: {project_ids}"
    )

    return project_ids


def ingest_readme(ti):
    project_ids = ti.xcom_pull(
        task_ids="load"
    )

    print(
        f"Ingesting README files for "
        f"{len(project_ids)} projects..."
    )

    ingest_readmes(project_ids)

    print("README ingestion completed.")

    return project_ids


def ai_enrichment(ti):
    from src.ingestion.enrich_projects import enrich_projects

    project_ids = ti.xcom_pull(
        task_ids="ingest_readme"
    )

    print(
        f"Running AI enrichment for "
        f"{len(project_ids)} projects..."
    )

    enrich_projects(project_ids)

    print("AI enrichment completed.")

    return project_ids


def create_embeddings_task(ti):
    from src.ingestion.create_chunks import create_embeddings

    project_ids = ti.xcom_pull(
        task_ids="ai_enrichment"
    )

    print(
        f"Creating embeddings for "
        f"{len(project_ids)} projects..."
    )

    create_embeddings(project_ids)

    print("Embedding creation completed.")

    return project_ids


with DAG(
    dag_id="project_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
) as dag:

    fetch = PythonOperator(
        task_id="fetch_github",
        python_callable=fetch_github,
    )

    filter_data = PythonOperator(
        task_id="incremental_filter",
        python_callable=incremental_filter,
    )

    transform_data = PythonOperator(
        task_id="transform",
        python_callable=transform,
    )

    validate_data = PythonOperator(
        task_id="validate",
        python_callable=validate,
    )

    load_data = PythonOperator(
        task_id="load",
        python_callable=load,
    )

    ingest_readme_data = PythonOperator(
        task_id="ingest_readme",
        python_callable=ingest_readme,
    )

    enrich = PythonOperator(
        task_id="ai_enrichment",
        python_callable=ai_enrichment,
    )

    embeddings = PythonOperator(
        task_id="create_embeddings",
        python_callable=create_embeddings_task,
    )

    fetch >> filter_data >> transform_data >> validate_data
    validate_data >> load_data >> ingest_readme_data
    ingest_readme_data >> enrich >> embeddings