import json
import os
import time
from datetime import datetime
import requests
from dotenv import load_dotenv
from ..db import get_db_connection

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

API_URL = "https://api.github.com/search/repositories"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28",
}


def fetch_repositories(
    query="topic:artificial-intelligence",
    total=50,
    sort="stars",
    order="desc",
):
    repositories = []
    page = 1

    while len(repositories) < total:
        remaining = total - len(repositories)

        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": min(10, remaining),
            "page": page,
        }

        try:
            response = requests.get(
                API_URL,
                headers=HEADERS,
                params=params,
                timeout=30,
            )

            # Handle rate limit
            if response.status_code == 403:
                reset_time = response.headers.get("X-RateLimit-Reset")

                if reset_time:
                    wait_time = max(int(reset_time) - int(time.time()), 0)
                    print(f"Rate limit reached. Waiting {wait_time} seconds...")
                    time.sleep(wait_time + 1)
                    continue

                raise Exception("GitHub API rate limit exceeded.")

            # Handle other HTTP errors
            response.raise_for_status()

            data = response.json()

            items = data.get("items", [])

            github_ids = [
                repo["id"]
                for repo in items
            ]

            existing_ids = get_existing_github_ids(github_ids)

            new_items = [
                repo
                for repo in items
                if repo["id"] not in existing_ids
            ]

            repositories.extend(new_items)

            print(
                f"Page {page}: "
                f"fetched {len(items)}, "
                f"existing {len(existing_ids)}, "
                f"new {len(new_items)}, "
                f"total new {len(repositories)}"
            )

            page += 1

            time.sleep(1)

        except requests.exceptions.Timeout:
            print("Request timed out. Retrying...")
            time.sleep(3)

        except requests.exceptions.ConnectionError:
            print("Connection error. Retrying...")
            time.sleep(3)

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            break

    return repositories[:total]


def save_raw_data(data):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"data/raw/repositories_{timestamp}.json"

    os.makedirs("data/raw", exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(
        f"Saved {len(data)} repositories "
        f"to {output_file}"
    )

    return output_file

def get_existing_github_ids(github_ids):
    if not github_ids:
        return set()

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT github_id
        FROM projects
        WHERE github_id = ANY(%s);
    """

    try:
        cursor.execute(query, (github_ids,))
        rows = cursor.fetchall()

        return {row[0] for row in rows}

    finally:
        cursor.close()
        conn.close()


def main():
    repositories = fetch_repositories(
        query="topic:artificial-intelligence",
        total=50,
    )

    save_raw_data(repositories)


if __name__ == "__main__":
    main()