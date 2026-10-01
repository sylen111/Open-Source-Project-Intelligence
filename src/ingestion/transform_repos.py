from datetime import datetime
import json
import os

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
    required_fields = [
        "github_id",
        "name",
        "full_name",
    ]

    for field in required_fields:
        if not repo.get(field):
            return False

    if not isinstance(repo["github_id"], int):
        return False

    if not isinstance(repo["stars"], int):
        return False

    if repo["stars"] < 0:
        return False

    return True


def validate_repositories(repositories):
    valid = []
    invalid = []

    for repo in repositories:
        if validate_repository(repo):
            valid.append(repo)
        else:
            invalid.append(repo)

    return valid, invalid

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