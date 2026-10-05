from src.ingestion.transform_repos import (
    validate_repositories,
    generate_data_quality_report,
    remove_duplicate_repositories,
)


repositories = [
    # Valid
    {
        "github_id": 1,
        "name": "valid-repo",
        "full_name": "user/valid-repo",
        "stars": 100,
        "forks": 10,
        "open_issues": 2,
        "topics": ["ai", "python"],
    },

    # Missing name
    {
        "github_id": 2,
        "name": "",
        "full_name": "user/missing-name",
        "stars": 50,
        "forks": 5,
        "open_issues": 1,
        "topics": [],
    },

    # Negative stars
    {
        "github_id": 3,
        "name": "bad-stars",
        "full_name": "user/bad-stars",
        "stars": -10,
        "forks": 5,
        "open_issues": 1,
        "topics": [],
    },

    # Invalid topics
    {
        "github_id": 4,
        "name": "bad-topics",
        "full_name": "user/bad-topics",
        "stars": 10,
        "forks": 2,
        "open_issues": 1,
        "topics": "ai,python",
    },

    # Duplicate github_id
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


def test_validate_repositories():
    valid, invalid = validate_repositories(repositories)

    assert len(valid) == 2
    assert len(invalid) == 3


def test_remove_duplicate_repositories():
    unique_repositories = remove_duplicate_repositories(
        repositories
    )

    assert len(unique_repositories) == 4

    github_ids = [
        repo["github_id"]
        for repo in unique_repositories
    ]

    assert github_ids.count(1) == 1


def test_generate_data_quality_report():
    report = generate_data_quality_report(repositories)

    assert report["total"] == 5
    assert report["valid"] == 2
    assert report["invalid"] == 3