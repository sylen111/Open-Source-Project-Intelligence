from src.ingestion.fetch_repos import filter_new_or_changed_repositories


repositories = [
    # 1. Unchanged
    {
        "id": 574523116,
        "updated_at": "2026-09-28T12:58:43Z",
    },

    # 2. Changed
    {
        "id": 1270363362,
        "updated_at": "2026-09-29T12:58:43Z",
    },

    # 3. New
    {
        "id": 999999999999,
        "updated_at": "2026-10-03T12:00:00Z",
    },
]


result = filter_new_or_changed_repositories(repositories)

print("\nSelected repositories:")

for repo in result:
    print(repo["id"], repo["updated_at"])