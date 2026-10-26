import sqlite3
from pathlib import Path

from alembic.script import ScriptDirectory

from app.db.migrate import DEFAULT_SCRIPT_LOCATION, build_config, current_revision, run_migrations


def real_head() -> str:
    config = build_config(Path("unused.db"), DEFAULT_SCRIPT_LOCATION)
    return ScriptDirectory.from_config(config).get_current_head()


def dump(database_path: Path, query: str) -> list[tuple]:
    with sqlite3.connect(database_path) as connection:
        return connection.execute(query).fetchall()


def test_restart_keeps_recipes_tags_and_links(tmp_path):
    database_path = tmp_path / "app.db"
    run_migrations(database_path)
    with sqlite3.connect(database_path) as connection:
        connection.execute("INSERT INTO recipes (nr, name, ingredients) VALUES (1, 'Soup', 'water\nsalt')")
        connection.execute("INSERT INTO tags (name, name_key) VALUES ('Quick', 'quick')")
        connection.execute("INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (1, 1)")
    tables = ("recipes", "tags", "recipe_tags")
    before = {table: dump(database_path, f"SELECT * FROM {table}") for table in tables}

    run_migrations(database_path)

    assert current_revision(database_path) == real_head()
    assert {table: dump(database_path, f"SELECT * FROM {table}") for table in tables} == before
    assert before["recipe_tags"] == [(1, 1)]
    assert not list(tmp_path.glob("app.db.bak-*"))


def test_unversioned_database_with_data_is_upgraded_and_backed_up(tmp_path):
    database_path = tmp_path / "app.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE legacy (id INTEGER PRIMARY KEY, note TEXT)")
        connection.executemany("INSERT INTO legacy (note) VALUES (?)", [("a",), ("b",)])
    legacy_rows = dump(database_path, "SELECT * FROM legacy")

    run_migrations(database_path)

    assert current_revision(database_path) == real_head()
    assert dump(database_path, "SELECT * FROM legacy") == legacy_rows
    assert dump(database_path, "SELECT name FROM sqlite_master WHERE name = 'recipes'") == [("recipes",)]
    backup = tmp_path / "app.db.bak-base"
    assert dump(backup, "SELECT * FROM legacy") == legacy_rows
