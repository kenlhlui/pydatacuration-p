"""Test that the shared tables are scoped by project_number (db/base.py)."""

from datetime import datetime
from datetime import timedelta
from pathlib import Path

import pytest
from sqlmodel import select

from pydatacuration.db import DatabaseBackend
from pydatacuration.db import get_database


@pytest.fixture
def db_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a DuckDB file with two projects that share the same checklist item and check IDs.

    P-1 has 2 checklist items and P-2 has 3, so leaked rows show up in the counts.

    Returns:
        Path: The DuckDB file.
    """
    monkeypatch.setenv('DB_TYPE', 'duckdb')
    db_file = tmp_path / 'db.duckdb'
    db = get_database(db_file=db_file)
    db.create_database()
    db.create_tables()
    models = db.models

    for project_number, n_items in (('P-1', 2), ('P-2', 3)):
        db.merge_records_to_table(
            models.project_metadata_record()(
                project_number=project_number,
                dataset_id=1,
                datasetid=1,
                last_modified_datetime=datetime(2026, 1, 1),  # noqa: DTZ001 - column is naive DATETIME
            )
        )
        db.merge_records_to_table(models.checklist_metadata()(project_number=project_number, name=project_number))
        for i in range(n_items):
            db.merge_records_to_table(models.checklist()(project_number=project_number, id=f'1.{i}', status='TBD'))
        db.merge_records_to_table(
            models.check_results()(
                project_number=project_number,
                check_id='c1',
                check_name=project_number,
                description='',
                unit='',
                results=[project_number],
            )
        )
    return db_file


def _db(db_file: Path, project_number: str) -> DatabaseBackend:
    return get_database(db_file=db_file, project_number=project_number)


def _project_numbers_per_table(db_file: Path) -> dict[str, set[str]]:
    db = get_database(db_file=db_file)
    models = db.models
    tables = (models.project_metadata_record(), models.checklist_metadata(), models.checklist(), models.check_results())
    with db.get_readonly_connection() as (session, _engine):
        return {model.__tablename__: set(session.exec(select(model.project_number)).all()) for model in tables}


def test_reads_are_scoped(db_file: Path) -> None:
    """Test that every read only returns the bound project's rows."""
    db = _db(db_file, 'P-1')
    check_results_model = db.models.check_results()

    assert db.read_project_metadata_record()['project_number'] == 'P-1'
    assert db.read_checklist_metadata()['name'] == 'P-1'
    assert [item.id for item in db.read_checklist()] == ['1.0', '1.1']
    assert db.get_status_count() == {'TBD': 2}
    assert [r['check_name'] for r in db.read_check_results()['check_results']] == ['P-1']
    assert db.read_row(check_results_model, 'check_id', 'c1')['results'] == ['P-1']
    assert [r['results'] for r in db.read_with_in_filter(check_results_model, 'check_id', ['c1'])] == [['P-1']]


def test_update_checklist_item_only_touches_own_project(db_file: Path) -> None:
    """Test that updating item 1.0 in P-1 leaves item 1.0 in P-2 unchanged."""
    p1, p2 = _db(db_file, 'P-1'), _db(db_file, 'P-2')

    assert p1.update_checklist_item('1.0', status='P', comments='done', time_spent=timedelta(minutes=2))

    assert p1.get_status_count() == {'P': 1, 'TBD': 1}
    assert p1.get_comment_input_count() == 1
    assert p1.get_time_spent_input_count() == 1
    assert p2.get_status_count() == {'TBD': 3}
    assert p2.get_comment_input_count() == 0
    assert p2.get_time_spent_input_count() == 0


def test_delete_project(db_file: Path) -> None:
    """Test that delete_project clears one project from all 4 tables and keeps the other."""
    get_database(db_file=db_file).delete_project('P-1')

    assert _project_numbers_per_table(db_file) == {
        'project_metadata': {'P-2'},
        'checklist_metadata': {'P-2'},
        'checklist': {'P-2'},
        'check_results': {'P-2'},
    }


def test_update_project_metadata_timestamp_with_child_rows(db_file: Path) -> None:
    """Test that the parent row can be updated while child rows reference it (DuckDB FK limitation guard)."""
    db = _db(db_file, 'P-1')
    initial = datetime(2026, 1, 1)  # noqa: DTZ001 - column is naive DATETIME

    db.update_project_metadata_timestamp()

    assert db.read_project_metadata_record(mode='python')['last_modified_datetime'] > initial
    assert _db(db_file, 'P-2').read_project_metadata_record(mode='python')['last_modified_datetime'] == initial
