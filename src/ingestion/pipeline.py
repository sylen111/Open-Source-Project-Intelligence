import json

from .transform_repos import (
    transform_repositories,
    validate_repositories,
)
from .load_projects import insert_projects


def load_raw_data(input_file):
    with open(input_file, "r", encoding="utf-8") as f:
        return json.load(f)


def process_repositories(raw_repositories):
    """
    Transform, validate, and load repositories into PostgreSQL.

    Returns:
        List of PostgreSQL project IDs.
    """
    print("Transform: cleaning data...")
    transformed = transform_repositories(raw_repositories)

    print("Validate: checking data...")
    valid, invalid = validate_repositories(transformed)

    print(f"Valid repositories: {len(valid)}")
    print(f"Invalid repositories: {len(invalid)}")

    if not valid:
        return []

    print("Load: inserting into PostgreSQL...")
    project_ids = insert_projects(valid)

    return project_ids


def run_pipeline(input_file):
    """
    Run the ETL pipeline using the given raw JSON file.
    """
    print(f"Extract: loading {input_file}...")

    raw_repositories = load_raw_data(input_file)

    print(f"Raw repositories: {len(raw_repositories)}")

    project_ids = process_repositories(raw_repositories)

    print(f"Processed project IDs: {project_ids}")
    print("ETL pipeline completed.")

    return project_ids