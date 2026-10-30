"""Test reading project metadata across all schemas (db/base.py and frontend/helpers.py)."""

from datetime import datetime
from pathlib import Path

import pytest

from pydatacuration.db import DatabaseBackend
from pydatacuration.db import get_database
from pydatacuration.frontend import helpers
from pydatacuration.frontend.helpers import NiceGUIHelper
from pydatacuration.utils.directory_manager import DirectoryManager


@pytest.fixture
def main_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a DuckDB file with two projects that have metadata and one schema that has none.

    Returns:
        Path: The main directory containing db/db.duckdb.
    """
    monkeypatch.setenv('DB_TYPE', 'duckdb')
    db_file = tmp_path / 'db' / DirectoryManager.DB_FILE_NAME
    db_file.parent.mkdir()

    for i, project_number in enumerate(['P-001', 'P-002'], start=1):
        db = get_database(schema_name=project_number, db_file=db_file)
        db.create_schema()
        project_metadata = db.models.project_metadata_record()
        db.merge_records_to_table(
            project_metadata(
                project_number=project_number,
                curator_name='curator',
                dataset_title=f'title {i}',
                dataset_pid=f'doi:10.0/{i}',
                dataset_id=i,
                datasetid=i,
                dataset_url=f'https://example.org/{i}',
                last_modified_datetime=datetime(2026, 1, i, 12, 30),  # noqa: DTZ001 - column is naive DATETIME
            )
        )

    get_database(schema_name='P-003', db_file=db_file).create_schema()
    return tmp_path


def _system_db(main_dir: Path) -> DatabaseBackend:
    return get_database(schema_name='_system_query_', db_file=main_dir / 'db' / DirectoryManager.DB_FILE_NAME)


def test_read_all_project_metadata_records(main_dir: Path) -> None:
    """Test that one query returns a record per schema with metadata, tagged with its schema name."""
    records = _system_db(main_dir).read_all_project_metadata_records()

    by_schema = {r['schema_name']: r for r in records}
    assert set(by_schema) == {'P-001', 'P-002'}
    assert by_schema['P-002']['dataset_title'] == 'title 2'
    assert by_schema['P-002']['last_modified_datetime'] == datetime(2026, 1, 2, 12, 30)  # noqa: DTZ001


def test_read_all_project_metadata_records_empty_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a database with no project_metadata tables returns an empty list."""
    monkeypatch.setenv('DB_TYPE', 'duckdb')
    db = get_database(schema_name='_system_query_', db_file=tmp_path / 'empty.duckdb')
    db.create_database()

    assert db.read_all_project_metadata_records() == []


def test_get_all_schemas(main_dir: Path) -> None:
    """Test formatting, the fallback row for a schema without metadata, and sort order."""
    schemas = NiceGUIHelper.get_all_schemas(main_dir)

    assert [s['project_number'] for s in schemas] == ['P-003', 'P-002', 'P-001']
    assert schemas[0] == {'project_number': 'P-003', 'name': 'P-003', 'last_modified': 'Unknown', 'has_metadata': False}
    assert schemas[1]['last_modified'] == '2026-01-02 12:30:00'
    assert schemas[1]['curator_name'] == 'curator'
    assert 'schema_name' not in schemas[1]


def test_get_all_schemas_creates_single_backend(main_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that listing projects does not create a backend per schema (n+1 regression guard)."""
    calls = []
    monkeypatch.setattr(helpers, 'get_database', lambda **kw: calls.append(kw) or get_database(**kw))

    NiceGUIHelper.get_all_schemas(main_dir)

    assert len(calls) == 1


def test_get_all_schemas_missing_db_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a missing DuckDB file returns an empty list."""
    monkeypatch.setenv('DB_TYPE', 'duckdb')

    assert NiceGUIHelper.get_all_schemas(tmp_path) == []
