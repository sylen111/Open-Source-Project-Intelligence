def test_database_connection(test_db):
    cursor = test_db.cursor()

    cursor.execute(
        """
        SELECT github_id, updated_at
        FROM projects
        ORDER BY github_id;
        """
    )

    rows = cursor.fetchall()

    cursor.close()

    assert len(rows) == 2
    assert rows[0][0] == 574523116
    assert rows[1][0] == 1270363362