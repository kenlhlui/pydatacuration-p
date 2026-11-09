"""Test scripts/db_migration.py: old per-project schemas are copied and their timestamps converted to UTC."""

import importlib.util
from datetime import date
from datetime import datetime
from pathlib import Path

import pytest
from sqlmodel import text

from pydatacuration.db import get_database
from pydatacuration.db.sqlmodels import Checklist
from pydatacuration.db.sqlmodels import ProjectMetadata


SCRIPT = Path(__file__).parents[1] / 'scripts' / 'db_migration.py'
spec = importlib.util.spec_from_file_location('db_migration', SCRIPT)
assert spec
assert spec.loader
db_migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(db_migration)


@pytest.fixture
def old_db_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a DuckDB file with one project in the old layout, with naive Toronto timestamps.

    Returns:
        Path: The DuckDB file.
    """
    monkeypatch.setenv('DB_TYPE', 'duckdb')
    db_file = tmp_path / 'db.duckdb'
    db = get_database(db_file=db_file)
    db.create_database()
    db.create_tables()

    # Write the rows to the new tables, then move them into an old-style schema.
    db.merge_records_to_table(
        ProjectMetadata(
            project_number='OLD-1',
            dataset_id=1,
            datasetid=1,
            # An evening in Toronto, so the UTC date is the next day.
            log_init_date=date(2026, 1, 10),
            log_last_update_date=date(2026, 1, 15),
            last_modified_datetime=datetime(2026, 1, 15, 21, 0),  # noqa: DTZ001 - old column is naive local time
        )
    )
    for item_id, ts in (('winter', datetime(2026, 1, 15, 12, 0)), ('summer', datetime(2026, 7, 15, 12, 0))):  # noqa: DTZ001
        db.merge_records_to_table(Checklist(project_number='OLD-1', id=item_id, last_modified_datetime=ts))

    with db.get_connection() as (_session, engine), engine.begin() as conn:
        conn.execute(text('CREATE SCHEMA "OLD-1"'))
        conn.execute(text('CREATE TABLE "OLD-1".project_metadata AS SELECT * FROM main.project_metadata'))
        for name in ('checklist_metadata', 'checklist', 'check_results'):
            conn.execute(text(f'CREATE TABLE "OLD-1".{name} AS SELECT * EXCLUDE (project_number) FROM main.{name}'))
    db.delete_project('OLD-1')
    return db_file


def test_migration_converts_timestamps_to_utc(old_db_file: Path) -> None:
    """Test that naive Toronto times become naive UTC times, with daylight saving time handled."""
    db_migration.main(db_file=old_db_file, source_tz='America/Toronto')

    db = get_database(db_file=old_db_file, project_number='OLD-1')
    project = db.read_project_metadata_record(mode='python')
    assert project['last_modified_datetime'] == datetime(2026, 1, 16, 2, 0)  # noqa: DTZ001
    assert project['log_last_update_date'] == date(2026, 1, 16)  # The UTC date of last_modified_datetime
    assert project['log_init_date'] == date(2026, 1, 10)  # No time of day: copied as is
    with db.get_readonly_connection() as (_session, engine), engine.connect() as conn:
        rows = dict(conn.execute(text('SELECT id, last_modified_datetime FROM main.checklist')).all())
    assert rows == {
        'winter': datetime(2026, 1, 15, 17, 0),  # noqa: DTZ001 - EST, UTC-5
        'summer': datetime(2026, 7, 15, 16, 0),  # noqa: DTZ001 - EDT, UTC-4
    }


def test_migration_rejects_unknown_time_zone(old_db_file: Path) -> None:
    """Test that a misspelt time zone stops the run before anything is copied."""
    with pytest.raises(Exception, match='Not/AZone'):
        db_migration.main(db_file=old_db_file, source_tz='Not/AZone')
