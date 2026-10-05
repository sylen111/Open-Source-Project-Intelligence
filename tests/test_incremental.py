from src.ingestion.fetch_repos import (
    filter_new_or_changed_repositories,
)


def test_filter_new_or_changed_repositories(
    test_db,
):

    repositories = [
        # Unchanged
        {
            "id": 574523116,
            "updated_at": "2026-09-28T12:58:43Z",
        },

        # Changed
        {
            "id": 1270363362,
            "updated_at": "2026-09-29T12:58:43Z",
        },

        # New
        {
            "id": 999999999,
            "updated_at": "2026-10-03T12:00:00Z",
        },
    ]

    result = filter_new_or_changed_repositories(
        repositories
    )

    result_ids = {
        repo["id"]
        for repo in result
    }

    assert 574523116 not in result_ids
    assert 1270363362 in result_ids
    assert 999999999 in result_ids