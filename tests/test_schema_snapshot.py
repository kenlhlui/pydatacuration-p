"""Test that the table layout only changes together with SCHEMA_VERSION.

Each schema version has a snapshot of its CREATE TABLE statements in tests/schema_snapshots/, one file per dialect.
If a model change makes this test fail, the layout has changed: bump SCHEMA_VERSION, make scripts/db_migration.py
handle the change, and create the snapshot for the new version:

    UPDATE_SCHEMA_SNAPSHOT=1 uv run pytest tests/test_schema_snapshot.py

Never edit the snapshot of an earlier version: it records what databases at that version look like.
"""

import os
from pathlib import Path

import pytest
from duckdb_engine import Dialect as DuckDBDialect
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Dialect
from sqlalchemy.schema import CreateTable
from sqlmodel import SQLModel

from pydatacuration.db.sqlmodels import SCHEMA_VERSION


SNAPSHOT_DIR = Path(__file__).parent / 'schema_snapshots'
DIALECTS: dict[str, Dialect] = {'postgresql': postgresql.dialect(), 'duckdb': DuckDBDialect()}


def render_schema(dialect: Dialect) -> str:
    """Return the CREATE TABLE statements of every table, parents before children.

    Trailing spaces are stripped, so an editor that trims whitespace does not break the snapshot.

    Returns:
        str: The statements, separated by blank lines.
    """
    statements = (str(CreateTable(table).compile(dialect=dialect)).strip() for table in SQLModel.metadata.sorted_tables)
    text = '\n\n'.join(f'{statement};' for statement in statements)
    return '\n'.join(line.rstrip() for line in text.splitlines()) + '\n'


@pytest.mark.parametrize('dialect_name', DIALECTS)
def test_schema_matches_snapshot(dialect_name: str) -> None:
    """Test that the models still produce the snapshot of the current SCHEMA_VERSION."""
    snapshot = SNAPSHOT_DIR / f'v{SCHEMA_VERSION}.{dialect_name}.sql'
    schema = render_schema(DIALECTS[dialect_name])

    if not snapshot.exists():
        if os.environ.get('UPDATE_SCHEMA_SNAPSHOT'):
            snapshot.parent.mkdir(exist_ok=True)
            snapshot.write_text(schema, encoding='utf-8')
        pytest.fail(
            f'No snapshot for schema version {SCHEMA_VERSION}: {snapshot}. '
            'Create it with: UPDATE_SCHEMA_SNAPSHOT=1 uv run pytest tests/test_schema_snapshot.py'
        )

    assert schema == snapshot.read_text(encoding='utf-8'), (
        f'The table layout no longer matches schema version {SCHEMA_VERSION}. Bump SCHEMA_VERSION in '
        'pydatacuration/db/sqlmodels.py, make scripts/db_migration.py handle the change, then create the new '
        'snapshot with: UPDATE_SCHEMA_SNAPSHOT=1 uv run pytest tests/test_schema_snapshot.py. '
        f'Do not edit {snapshot.name}.'
    )
