from src.ingestion.transform_repos import (
    validate_repositories,
    generate_data_quality_report,
    remove_duplicate_repositories,
)

repositories = [
    # 1. Valid
    {
        "github_id": 1,
        "name": "valid-repo",
        "full_name": "user/valid-repo",
        "stars": 100,
        "forks": 10,
        "open_issues": 2,
        "topics": ["ai", "python"],
    },

    # 2. Missing name
    {
        "github_id": 2,
        "name": "",
        "full_name": "user/missing-name",
        "stars": 50,
        "forks": 5,
        "open_issues": 1,
        "topics": [],
    },

    # 3. Negative stars
    {
        "github_id": 3,
        "name": "bad-stars",
        "full_name": "user/bad-stars",
        "stars": -10,
        "forks": 5,
        "open_issues": 1,
        "topics": [],
    },

    # 4. Invalid topics
    {
        "github_id": 4,
        "name": "bad-topics",
        "full_name": "user/bad-topics",
        "stars": 10,
        "forks": 2,
        "open_issues": 1,
        "topics": "ai,python",
    },
    {
    "github_id": 1,
    "name": "duplicate-repo",
    "full_name": "user/duplicate-repo",
    "stars": 20,
    "forks": 1,
    "open_issues": 0,
    "topics": [],
    },
]


valid, invalid = validate_repositories(repositories)
unique_repositories = remove_duplicate_repositories(repositories)

print("\nDuplicate Test:")
print(f"Original: {len(repositories)}")
print(f"After removing duplicates: {len(unique_repositories)}")
print(
    f"Duplicates removed: "
    f"{len(repositories) - len(unique_repositories)}"
)

print("Valid:", len(valid))
print("Invalid:", len(invalid))

print("\nInvalid repositories:")

for item in invalid:
    print(
        item["repo"]["name"],
        "->",
        item["errors"]
    )

report = generate_data_quality_report(repositories)

print("\nData Quality Report")
print("-------------------")
print(f"Total: {report['total']}")
print(f"Valid: {report['valid']}")
print(f"Invalid: {report['invalid']}")

print("\nErrors:")

for error, count in report["errors"].items():
    print(f"{error} -> {count}")