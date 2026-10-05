import os

import psycopg2
import pytest
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture
def test_db():
    conn = psycopg2.connect(
        host="localhost",
        port=5434,
        database="ai_project_test_db",
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

    cursor = conn.cursor()

    cursor.execute("DELETE FROM projects;")

    cursor.execute(
        """
        INSERT INTO projects (
            github_id,
            name,
            full_name,
            updated_at
        )
        VALUES
            (
                574523116,
                'test-unchanged',
                'test/test-unchanged',
                '2026-09-28 12:58:43'
            ),
            (
                1270363362,
                'test-changed',
                'test/test-changed',
                '2026-09-28 12:58:43'
            );
        """
    )

    conn.commit()

    cursor.close()

    yield conn

    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects;")
    conn.commit()
    cursor.close()

    conn.close()