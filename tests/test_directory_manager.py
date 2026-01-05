"""Test the directory_manager.py module."""

from pathlib import Path

import pytest

from pydatacuration.directory_manager import DirectoryManager


@pytest.mark.parametrize(
    ('main_dir', 'ticket_number', 'expected_project_dir'),
    [
        ('/home/user/projects', 'TICKET-123', '/home/user/projects/projects/TICKET-123'),
        ('/data/main_dir', 'PROJECT-456', '/data/main_dir/projects/PROJECT-456'),
        (None, 'WORK-789', str(Path.cwd() / 'projects' / 'WORK-789')),
        ('/var/data/projects/TICKET-000', 'TICKET-000', '/var/data/projects/TICKET-000'),
    ],
)
def test_define_project_dir(main_dir: str | None, ticket_number: str, expected_project_dir: str) -> None:
    """Test the _define_project_dir method of DirectoryManager.

    Args:
        main_dir (str | None): The main directory path.
        ticket_number (str): The ticket number.
        expected_project_dir (str): The expected project directory path.

    Returns:
        None: This test does not return anything.

    """
    dir_manager = DirectoryManager(ticket_number=ticket_number, main_dir=main_dir or Path.cwd(), res_dir=None)
    project_dir = dir_manager._define_project_dir()
    assert str(project_dir) == expected_project_dir


@pytest.mark.parametrize(
    ('main_dir', 'expected_db_dir'),
    [
        ('/home/user/projects', '/home/user/projects/db'),
        ('/data/main_dir', '/data/main_dir/db'),
        (None, str(Path.cwd() / 'db')),
    ],
)
def test_define_db_dir(main_dir: str | None, expected_db_dir: str) -> None:
    """Test the _define_db_dir method of DirectoryManager.

    Args:
        main_dir (str | None): The main directory path.
        expected_db_dir (str): The expected database directory path.

    Returns:
        None: This test does not return anything.

    """
    dir_manager = DirectoryManager(ticket_number='TEST-001', main_dir=main_dir or Path.cwd(), res_dir=None)
    db_dir = dir_manager._define_db_dir()
    assert str(db_dir) == expected_db_dir


@pytest.mark.parametrize(
    ('main_dir', 'expected_db_path'),
    [
        ('/home/user/projects', '/home/user/projects/db/duckdb.db'),
        ('/data/main_dir', '/data/main_dir/db/duckdb.db'),
        (None, str(Path.cwd() / 'db' / 'duckdb.db')),
    ],
)
def test_define_db_path(main_dir: str | None, expected_db_path: str) -> None:
    """Test the _define_db_path method of DirectoryManager.

    Args:
        main_dir (str | None): The main directory path.
        expected_db_path (str): The expected database file path.
    """
    dir_manager = DirectoryManager(ticket_number='TEST-002', main_dir=main_dir or Path.cwd(), res_dir=None)
    db_path = dir_manager._define_db_path()
    assert str(db_path) == expected_db_path
