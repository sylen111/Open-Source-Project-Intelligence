from datetime import datetime
import json
import os
from collections import Counter


OUTPUT_FILE = "data/transformed/repositories.json"

def clean_text(value):
    if value is None:
        return None

    value = value.strip()

    return value if value else None


def transform_repository(repo):
    owner = repo.get("owner", {}).get("login")

    license_info = repo.get("license")

    license_name = None

    if license_info:
        license_name = license_info.get("spdx_id")

    return {
        "github_id": repo.get("id"),
        "name": clean_text(repo.get("name")),
        "full_name": clean_text(repo.get("full_name")),
        "owner": clean_text(owner),
        "description": clean_text(repo.get("description")),
        "html_url": repo.get("html_url"),
        "homepage": clean_text(repo.get("homepage")),
        "language": clean_text(repo.get("language")),
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "open_issues": repo.get("open_issues_count", 0),
        "size": repo.get("size", 0),
        "is_fork": repo.get("fork", False),
        "archived": repo.get("archived", False),
        "license": license_name,
        "default_branch": repo.get("default_branch"),
        "created_at": repo.get("created_at"),
        "updated_at": repo.get("updated_at"),
        "pushed_at": repo.get("pushed_at"),
        "topics": repo.get("topics", []),
    }


def transform_repositories(repositories):
    return [
        transform_repository(repo)
        for repo in repositories
    ]

def validate_repository(repo):
    errors = []

    required_fields = [
        "github_id",
        "name",
        "full_name",
    ]

    # Completeness
    for field in required_fields:
        if not repo.get(field):
            errors.append(f"Missing required field: {field}")

    # Validity
    if "github_id" in repo and not isinstance(repo["github_id"], int):
        errors.append("github_id must be an integer")

    if "stars" in repo:
        if not isinstance(repo["stars"], int):
            errors.append("stars must be an integer")
        elif repo["stars"] < 0:
            errors.append("stars cannot be negative")

    if "forks" in repo:
        if not isinstance(repo["forks"], int):
            errors.append("forks must be an integer")
        elif repo["forks"] < 0:
            errors.append("forks cannot be negative")

    if "open_issues" in repo:
        if not isinstance(repo["open_issues"], int):
            errors.append("open_issues must be an integer")
        elif repo["open_issues"] < 0:
            errors.append("open_issues cannot be negative")

    if "topics" in repo and not isinstance(repo["topics"], list):
        errors.append("topics must be a list")

    return errors


def validate_repositories(repositories):
    valid = []
    invalid = []

    for repo in repositories:
        errors = validate_repository(repo)

        if not errors:
            valid.append(repo)
        else:
            invalid.append({
                "repo": repo,
                "errors": errors,
            })

    return valid, invalid


def remove_duplicate_repositories(repositories):
    seen = set()
    unique = []

    for repo in repositories:
        github_id = repo["github_id"]

        if github_id in seen:
            continue

        seen.add(github_id)
        unique.append(repo)

    return unique

def save_transformed_data(repositories):
    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True
    )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            repositories,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"Saved {len(repositories)} transformed repositories "
        f"to {OUTPUT_FILE}"
    )

def generate_data_quality_report(repositories):
    valid, invalid = validate_repositories(repositories)

    error_counts = Counter()

    for item in invalid:
        for error in item["errors"]:
            error_counts[error] += 1

    return {
        "total": len(repositories),
        "valid": len(valid),
        "invalid": len(invalid),
        "errors": dict(error_counts),
    }