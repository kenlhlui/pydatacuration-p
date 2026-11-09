"""Test the schema version check in get_database() (db/__init__.py) and its bookkeeping in db/base.py."""

from pathlib import Path

import pytest

from pydatacuration.db import get_database
from pydatacuration.db.sqlmodels import SCHEMA_VERSION
from pydatacuration.exceptions import SchemaVersionError


@pytest.fixture
def db_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Return the path of a DuckDB file that does not exist yet.

    Returns:
        Path: The DuckDB file.
    """
    monkeypatch.setenv('DB_TYPE', 'duckdb')
    return tmp_path / 'db.duckdb'


def test_new_database_gets_current_version(db_file: Path) -> None:
    """Test that a new database is accepted, and that create_tables() records the current version."""
    db = get_database(db_file=db_file)
    assert db.get_schema_version() is None
    db.create_database()
    db.create_tables()

    assert get_database(db_file=db_file).get_schema_version() == SCHEMA_VERSION


def test_create_tables_keeps_version(db_file: Path) -> None:
    """Test that create_tables() on an existing database does not overwrite its version."""
    db = get_database(db_file=db_file)
    db.create_database()
    db.create_tables()
    db.set_schema_version(1)

    db.create_tables()

    assert db.get_schema_version() == 1


def test_newer_database_is_refused(db_file: Path) -> None:
    """Test that an app older than the database refuses to open it."""
    db = get_database(db_file=db_file)
    db.create_database()
    db.create_tables()
    db.set_schema_version(SCHEMA_VERSION + 1)

    with pytest.raises(SchemaVersionError, match='Upgrade the app'):
        get_database(db_file=db_file)
