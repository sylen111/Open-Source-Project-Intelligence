import json

from .transform_repos import (
    transform_repositories,
    validate_repositories,
    remove_duplicate_repositories,
)
from .load_projects import insert_projects


def load_raw_data(input_file):
    with open(input_file, "r", encoding="utf-8") as f:
        return json.load(f)


def transform_data(raw_repositories):
    """
    Transform raw GitHub repositories.
    """
    print("Transform: cleaning data...")

    transformed = transform_repositories(raw_repositories)

    print(f"Transformed repositories: {len(transformed)}")

    return transformed


def validate_data(repositories):
    """
    Validate repositories and remove duplicates.

    Returns:
        List of valid, unique repositories.
    """
    print("Validate: checking data...")

    valid, invalid = validate_repositories(repositories)

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
        return []

    print("Quality: checking duplicates...")

    unique = remove_duplicate_repositories(valid)

    duplicates_removed = len(valid) - len(unique)

    print(f"Duplicates removed: {duplicates_removed}")

    return unique


def load_data(repositories):
    """
    Load validated repositories into PostgreSQL.

    Returns:
        List of PostgreSQL project IDs.
    """
    if not repositories:
        print("No repositories to load.")
        return []

    print("Load: inserting into PostgreSQL...")

    project_ids = insert_projects(repositories)

    print(f"Loaded project IDs: {project_ids}")

    return project_ids


def process_repositories(raw_repositories):
    """
    Transform, validate, and load repositories into PostgreSQL.

    Returns:
        List of PostgreSQL project IDs.
    """
    transformed = transform_data(raw_repositories)

    valid_repositories = validate_data(transformed)

    project_ids = load_data(valid_repositories)

    return project_ids


def run_pipeline(input_file):
    """
    Run the complete ETL pipeline using the given raw JSON file.
    """
    print(f"Extract: loading {input_file}...")

    raw_repositories = load_raw_data(input_file)

    print(f"Raw repositories: {len(raw_repositories)}")

    project_ids = process_repositories(raw_repositories)

    print(f"Processed project IDs: {project_ids}")
    print("ETL pipeline completed.")

    return project_ids


if __name__ == "__main__":
    run_pipeline("data/raw/repositories.json")