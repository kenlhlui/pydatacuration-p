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


@pytest.mark.parametrize(
    ('dir_name', 'should_succeed'),
    [
        ('logs', True),
        ('dataset/files', True),
        ('dataset/metadata', True),
        ('dataset/temp', True),
        ('outputs', True),
        ('outputs/reports', True),
        ('db', True),
        ('nonexistent', False),
    ],
)
def test_get_dir(tmp_path: Path, dir_name: str, should_succeed: bool) -> None:
    """Test the get_dir method of DirectoryManager.

    Args:
        tmp_path (Path): Pytest fixture for temporary directory.
        dir_name (str): The directory name to retrieve.
        should_succeed (bool): Whether the retrieval should succeed.
    """
    dir_manager = DirectoryManager(ticket_number='TEST-003', main_dir=tmp_path, res_dir=None)

    if should_succeed:
        dir_path = dir_manager.get_dir(dir_name)
        assert isinstance(dir_path, Path)
        if dir_name == 'db':
            assert dir_path == tmp_path / 'db'
        else:
            expected_path = dir_manager.project_dir / dir_manager._directory_structure[dir_name]
            assert dir_path == expected_path
    else:
        with pytest.raises(KeyError, match=f"Directory '{dir_name}' not found in structure"):
            dir_manager.get_dir(dir_name)


def test_create_dir_predefined(tmp_path: Path) -> None:
    """Test creating a predefined directory.

    Args:
        tmp_path (Path): Pytest fixture for temporary directory.
    """
    dir_manager = DirectoryManager(ticket_number='TEST-004', main_dir=tmp_path, res_dir=None)
    created_dir = dir_manager.create_dir('logs')

    assert created_dir.exists()
    assert created_dir.is_dir()
    assert created_dir == dir_manager.project_dir / 'logs'


def test_create_dir_custom_path(tmp_path: Path) -> None:
    """Test creating a directory with a custom path.

    Args:
        tmp_path (Path): Pytest fixture for temporary directory.
    """
    dir_manager = DirectoryManager(ticket_number='TEST-005', main_dir=tmp_path, res_dir=None)
    custom_path = 'custom/nested/dir'
    created_dir = dir_manager.create_dir('custom_dir', custom_path=custom_path)

    assert created_dir.exists()
    assert created_dir.is_dir()
    assert created_dir == dir_manager.project_dir / custom_path


def test_create_dir_already_exists(tmp_path: Path) -> None:
    """Test creating a directory that already exists.

    Args:
        tmp_path (Path): Pytest fixture for temporary directory.
    """
    dir_manager = DirectoryManager(ticket_number='TEST-006', main_dir=tmp_path, res_dir=None)
    created_dir = dir_manager.create_dir('logs')
    created_dir_again = dir_manager.create_dir('logs')

    assert created_dir == created_dir_again
    assert created_dir.exists()


def test_create_dirs_predefined(tmp_path: Path) -> None:
    """Test creating multiple predefined directories.

    Args:
        tmp_path (Path): Pytest fixture for temporary directory.
    """
    dir_manager = DirectoryManager(ticket_number='TEST-007', main_dir=tmp_path, res_dir=None)
    dir_names = ['logs', 'outputs', 'dataset/files']
    created_dirs = dir_manager.create_dirs(dir_names=dir_names)

    assert len(created_dirs) == 3
    for name in dir_names:
        assert name in created_dirs
        assert created_dirs[name].exists()
        assert created_dirs[name].is_dir()


def test_create_dirs_custom(tmp_path: Path) -> None:
    """Test creating multiple custom directories.

    Args:
        tmp_path (Path): Pytest fixture for temporary directory.
    """
    dir_manager = DirectoryManager(ticket_number='TEST-008', main_dir=tmp_path, res_dir=None)
    custom_dirs = {'custom1': 'path1', 'custom2': 'path2/nested'}
    created_dirs = dir_manager.create_dirs(custom_dirs=custom_dirs)

    assert len(created_dirs) == 2
    assert created_dirs['custom1'] == dir_manager.project_dir / 'path1'
    assert created_dirs['custom2'] == dir_manager.project_dir / 'path2/nested'
    for dir_path in created_dirs.values():
        assert dir_path.exists()


def test_create_dirs_mixed(tmp_path: Path) -> None:
    """Test creating both predefined and custom directories.

    Args:
        tmp_path (Path): Pytest fixture for temporary directory.
    """
    dir_manager = DirectoryManager(ticket_number='TEST-009', main_dir=tmp_path, res_dir=None)
    dir_names = ['logs', 'outputs']
    custom_dirs = {'custom': 'custom/path'}
    created_dirs = dir_manager.create_dirs(dir_names=dir_names, custom_dirs=custom_dirs)

    assert len(created_dirs) == 3
    assert all(dir_path.exists() for dir_path in created_dirs.values())


def test_make_dirs(tmp_path: Path) -> None:
    """Test creating the default directory structure.

    Args:
        tmp_path (Path): Pytest fixture for temporary directory.
    """
    dir_manager = DirectoryManager(ticket_number='TEST-010', main_dir=tmp_path, res_dir=None)
    created_dirs = dir_manager.make_dirs()

    expected_dirs = ['logs', 'dataset/files', 'dataset/metadata', 'dataset/temp', 'outputs', 'db']
    assert len(created_dirs) == len(expected_dirs)

    for dir_name in expected_dirs:
        assert dir_name in created_dirs
        assert created_dirs[dir_name].exists()
        assert created_dirs[dir_name].is_dir()


def test_add_directory(tmp_path: Path) -> None:
    """Test adding a new directory to the structure.

    Args:
        tmp_path (Path): Pytest fixture for temporary directory.
    """
    dir_manager = DirectoryManager(ticket_number='TEST-011', main_dir=tmp_path, res_dir=None)
    initial_count = len(dir_manager._directory_structure)

    dir_manager.add_directory('new_dir', 'path/to/new_dir')

    assert len(dir_manager._directory_structure) == initial_count + 1
    assert 'new_dir' in dir_manager._directory_structure
    assert dir_manager._directory_structure['new_dir'] == 'path/to/new_dir'


def test_list_directories(tmp_path: Path) -> None:
    """Test listing all defined directories.

    Args:
        tmp_path (Path): Pytest fixture for temporary directory.
    """
    dir_manager = DirectoryManager(ticket_number='TEST-012', main_dir=tmp_path, res_dir=None)
    directories = dir_manager.list_directories()

    expected_dirs = {
        'logs': 'logs',
        'dataset/files': 'dataset/files',
        'dataset/metadata': 'dataset/metadata',
        'dataset/temp': 'dataset/temp',
        'outputs': 'outputs',
        'outputs/reports': 'outputs/reports',
    }

    assert directories == expected_dirs
    # Verify it returns a copy, not the original
    directories['test'] = 'test'
    assert 'test' not in dir_manager._directory_structure


def test_delete_dir_exists(tmp_path: Path) -> None:
    """Test deleting an existing directory.

    Args:
        tmp_path (Path): Pytest fixture for temporary directory.
    """
    test_dir = tmp_path / 'test_delete'
    test_dir.mkdir()
    assert test_dir.exists()

    DirectoryManager.delete_dir(test_dir)
    assert not test_dir.exists()


def test_delete_dir_not_exists(tmp_path: Path) -> None:
    """Test deleting a non-existent directory.

    Args:
        tmp_path (Path): Pytest fixture for temporary directory.
    """
    test_dir = tmp_path / 'nonexistent'
    assert not test_dir.exists()

    # Should not raise an error
    DirectoryManager.delete_dir(test_dir)
    assert not test_dir.exists()


def test_delete_dir_with_contents(tmp_path: Path) -> None:
    """Test deleting a directory with contents.

    Args:
        tmp_path (Path): Pytest fixture for temporary directory.
    """
    test_dir = tmp_path / 'test_with_contents'
    test_dir.mkdir()
    (test_dir / 'file1.txt').write_text('content')
    (test_dir / 'subdir').mkdir()
    (test_dir / 'subdir' / 'file2.txt').write_text('content')

    DirectoryManager.delete_dir(test_dir)
    assert not test_dir.exists()


def test_property_log_files_dir(tmp_path: Path) -> None:
    """Test the log_files_dir property.

    Args:
        tmp_path (Path): Pytest fixture for temporary directory.
    """
    dir_manager = DirectoryManager(ticket_number='TEST-013', main_dir=tmp_path, res_dir=None)
    assert dir_manager.log_files_dir == dir_manager.project_dir / 'logs'


def test_property_logs_dir(tmp_path: Path) -> None:
    """Test the logs_dir property.

    Args:
        tmp_path (Path): Pytest fixture for temporary directory.
    """
    dir_manager = DirectoryManager(ticket_number='TEST-014', main_dir=tmp_path, res_dir=None)
    assert dir_manager.logs_dir == dir_manager.project_dir / 'logs'


def test_property_db_dir(tmp_path: Path) -> None:
    """Test the db_dir property.

    Args:
        tmp_path (Path): Pytest fixture for temporary directory.
    """
    dir_manager = DirectoryManager(ticket_number='TEST-015', main_dir=tmp_path, res_dir=None)
    assert dir_manager.db_dir == tmp_path / 'db'


def test_property_db_path(tmp_path: Path) -> None:
    """Test the db_path property.

    Args:
        tmp_path (Path): Pytest fixture for temporary directory.
    """
    dir_manager = DirectoryManager(ticket_number='TEST-016', main_dir=tmp_path, res_dir=None)
    assert dir_manager.db_path == tmp_path / 'db' / 'duckdb.db'


def test_property_outputs_dir(tmp_path: Path) -> None:
    """Test the outputs_dir property.

    Args:
        tmp_path (Path): Pytest fixture for temporary directory.
    """
    dir_manager = DirectoryManager(ticket_number='TEST-017', main_dir=tmp_path, res_dir=None)
    assert dir_manager.outputs_dir == dir_manager.project_dir / 'outputs'


def test_property_metadata_dir(tmp_path: Path) -> None:
    """Test the metadata_dir property.

    Args:
        tmp_path (Path): Pytest fixture for temporary directory.
    """
    dir_manager = DirectoryManager(ticket_number='TEST-018', main_dir=tmp_path, res_dir=None)
    assert dir_manager.metadata_dir == dir_manager.project_dir / 'dataset/metadata'


def test_property_files_dir(tmp_path: Path) -> None:
    """Test the files_dir property.

    Args:
        tmp_path (Path): Pytest fixture for temporary directory.
    """
    dir_manager = DirectoryManager(ticket_number='TEST-019', main_dir=tmp_path, res_dir=None)
    assert dir_manager.files_dir == dir_manager.project_dir / 'dataset/files'


def test_property_main_dir_path(tmp_path: Path) -> None:
    """Test the main_dir_path property.

    Args:
        tmp_path (Path): Pytest fixture for temporary directory.
    """
    dir_manager = DirectoryManager(ticket_number='TEST-020', main_dir=tmp_path, res_dir=None)
    assert dir_manager.main_dir_path == tmp_path.resolve()
