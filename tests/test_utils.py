"""First test file."""

from pathlib import Path

import orjson
import pytest
import typer
from loguru import logger

from pydatacuration.utils import check_ds_read_access
from pydatacuration.utils import check_readme_file_existence
from pydatacuration.utils import check_ticket_num_input
from pydatacuration.utils import compare_files_and_metadata
from pydatacuration.utils import gen_tree_diagram
from pydatacuration.utils import orjson_export
from pydatacuration.utils import parse_dataset_url
from pydatacuration.utils import parse_file_list_metadata
from pydatacuration.utils import validate_api_token


@pytest.mark.parametrize(
    ('input_string', 'expected_bool'),
    [
        ('path/aReADme.md', True),
        ('README', True),
        ('another_path/subdir/0_README.pdf', True),
        ('readme', True),
        ('', False),
    ],
)
def test_check_readme_file_existence(input_string, expected_bool):
    """Test for README file existence checking function."""
    result_file, result_bool = check_readme_file_existence(input_string)
    assert result_file == input_string
    assert result_bool is expected_bool


def test_compare_files_and_metadata_identical(tmp_path):
    """Test compare_files_and_metadata with identical checksums."""
    # Create a logs directory for diff output
    logs_dir = tmp_path / 'logs'
    logs_dir.mkdir()

    dl_files_checksums = [
        {'file': 'data/file1.txt', 'md5_checksum': 'abc123'},
        {'file': 'data/file2.csv', 'md5_checksum': 'def456'},
    ]
    metadata_file_checksums = [
        {'file': 'data/file1.txt', 'md5_checksum': 'abc123'},
        {'file': 'data/file2.csv', 'md5_checksum': 'def456'},
    ]

    result = compare_files_and_metadata(dl_files_checksums, metadata_file_checksums, tmp_path)
    assert result is False


def test_compare_files_and_metadata_different(tmp_path):
    """Test compare_files_and_metadata with different checksums."""
    # Create a logs directory for diff output
    logs_dir = tmp_path / 'logs'
    logs_dir.mkdir()

    dl_files_checksums = [
        {'file': 'data/file1.txt', 'md5_checksum': 'abc123'},
        {'file': 'data/file2.csv', 'md5_checksum': 'wrong_checksum'},
    ]
    metadata_file_checksums = [
        {'file': 'data/file1.txt', 'md5_checksum': 'abc123'},
        {'file': 'data/file2.csv', 'md5_checksum': 'def456'},
    ]

    with pytest.raises(SystemExit) as exc_info:
        compare_files_and_metadata(dl_files_checksums, metadata_file_checksums, tmp_path)
    assert exc_info.value.code == 1

    # Check that diff.txt was created
    diff_file = tmp_path / 'logs' / 'diff.txt'
    assert diff_file.exists()


def test_compare_files_and_metadata_ignore_order(tmp_path):
    """Test compare_files_and_metadata ignores order."""
    # Create a logs directory for diff output
    logs_dir = tmp_path / 'logs'
    logs_dir.mkdir()

    dl_files_checksums = [
        {'file': 'data/file2.csv', 'md5_checksum': 'def456'},
        {'file': 'data/file1.txt', 'md5_checksum': 'abc123'},
    ]
    metadata_file_checksums = [
        {'file': 'data/file1.txt', 'md5_checksum': 'abc123'},
        {'file': 'data/file2.csv', 'md5_checksum': 'def456'},
    ]

    result = compare_files_and_metadata(dl_files_checksums, metadata_file_checksums, tmp_path)
    assert result is False


def test_gen_tree_diagram_success(tmp_path):
    """Test gen_tree_diagram successfully creates tree diagram file."""
    # Create a test directory structure
    target_dir = tmp_path / 'test_target'
    target_dir.mkdir()
    (target_dir / 'file1.txt').write_text('content1')
    (target_dir / 'file2.csv').write_text('content2')
    subdir = target_dir / 'subdir'
    subdir.mkdir()
    (subdir / 'file3.txt').write_text('content3')

    # Create save directory
    save_dir = tmp_path / 'save_location'
    save_dir.mkdir()

    # Run the function
    gen_tree_diagram(target_dir, save_dir)

    # Check that the tree file was created
    tree_file = save_dir / 'ds_tree.txt'
    assert tree_file.exists()

    # Check that the file has content
    content = tree_file.read_text()
    assert len(content) > 0


def test_gen_tree_diagram_nonexistent_dir(tmp_path):
    """Test gen_tree_diagram with non-existent target directory."""
    target_dir = tmp_path / 'nonexistent'
    save_dir = tmp_path / 'save_location'
    save_dir.mkdir()

    with pytest.raises(SystemExit) as exc_info:
        gen_tree_diagram(target_dir, save_dir)

    assert exc_info.value.code == 1


def test_parse_file_list_metadata():
    """Test parse_file_list_metadata function."""
    file_list_metadata = [
        {
            'dataFile': {
                'originalFileName': 'data.csv',
                'md5': 'abc123def456',
            },
            'directoryLabel': 'folder1/subfolder',
        },
        {
            'dataFile': {
                'filename': 'readme.txt',
                'md5': '789xyz321',
            },
            'directoryLabel': '',
        },
        {
            'dataFile': {
                'originalFileName': 'image.png',
                'filename': 'image_backup.png',
                'md5': 'img123hash',
            },
            'directoryLabel': 'images',
        },
    ]

    result = parse_file_list_metadata(file_list_metadata)

    expected = [
        {'file': 'folder1/subfolder/data.csv', 'md5_checksum': 'abc123def456'},
        {'file': 'readme.txt', 'md5_checksum': '789xyz321'},
        {'file': 'images/image.png', 'md5_checksum': 'img123hash'},
    ]

    assert result == expected


def test_parse_file_list_metadata_empty():
    """Test parse_file_list_metadata with empty list."""
    result = parse_file_list_metadata([])
    assert result == []


@pytest.mark.parametrize(
    'input_string',
    [
        'Ticket-12345',
        'ticket_2345',
        '12345',
        'ticket',
    ],
)
def test_check_ticket_num_input_valid(input_string):
    """Test for valid ticket number inputs."""
    result_string = check_ticket_num_input(input_string)
    assert result_string == input_string


@pytest.mark.parametrize(
    ('input_string', 'expected_error_msg'),
    [
        ('', 'Ticket number cannot be empty.'),
        ('A@9', 'Ticket number must only contain letters, numbers, hyphens, and underscores.'),
        ('ticket number', 'Ticket number must only contain letters, numbers, hyphens, and underscores.'),
        ('ticket#123', 'Ticket number must only contain letters, numbers, hyphens, and underscores.'),
    ],
)
def test_check_ticket_num_input_invalid(input_string, expected_error_msg):
    """Test that invalid ticket numbers raise typer.BadParameter."""
    with pytest.raises(typer.BadParameter, match=expected_error_msg):
        check_ticket_num_input(input_string)


def test_check_ds_read_access():
    """Placeholder for future test of check_ds_read_access function."""
    # TODO: Implement this test in the future


def test_validate_api_token_with_env_var(monkeypatch):
    """Test validate_api_token returns env var when value is empty string."""
    monkeypatch.setenv('API_TOKEN', 'env_token_12345')
    result = validate_api_token('')
    assert result == 'env_token_12345'


def test_validate_api_token_with_value(monkeypatch):
    """Test validate_api_token returns provided value when not empty."""
    monkeypatch.setenv('API_TOKEN', 'env_token_12345')
    result = validate_api_token('my_custom_token')
    assert result == 'my_custom_token'


def test_validate_api_token_empty_no_env(monkeypatch):
    """Test validate_api_token returns empty string when no env var exists."""
    monkeypatch.delenv('API_TOKEN', raising=False)
    result = validate_api_token('')
    assert not result  # Should be empty string


def test_validate_api_token_none_value():
    """Test validate_api_token returns None when value is None."""
    result = validate_api_token(None)
    assert result is None


def test_orjson_export_success(tmp_path):
    """Test orjson_export successfully writes JSON file."""
    file_path = tmp_path / 'test_output.json'
    test_data = {
        'name': 'Test Dataset',
        'version': '1.0',
        'files': ['file1.txt', 'file2.csv'],
        'count': 42,
    }

    orjson_export(file_path, test_data)

    # Check file exists
    assert file_path.exists()

    # Read and verify content
    with file_path.open('rb') as f:
        loaded_data = orjson.loads(f.read())
    assert loaded_data == test_data


def test_orjson_export_with_string_path(tmp_path):
    """Test orjson_export works with string path."""
    file_path = str(tmp_path / 'test_output.json')
    test_data = {'key': 'value'}

    orjson_export(file_path, test_data)

    # Check file exists
    assert Path(file_path).exists()


def test_orjson_export_nested_data(tmp_path):
    """Test orjson_export handles nested data structures."""
    file_path = tmp_path / 'nested.json'
    test_data = {
        'metadata': {
            'author': 'Test User',
            'tags': ['data', 'science', 'test'],
        },
        'files': [
            {'name': 'file1.txt', 'size': 1024},
            {'name': 'file2.csv', 'size': 2048},
        ],
    }

    orjson_export(file_path, test_data)

    # Verify content
    with file_path.open('rb') as f:
        loaded_data = orjson.loads(f.read())
    assert loaded_data == test_data


def test_orjson_export_invalid_path():
    """Test orjson_export raises exception for invalid path."""
    invalid_path = '/nonexistent/directory/file.json'
    test_data = {'key': 'value'}

    with pytest.raises(Exception):
        orjson_export(invalid_path, test_data)


@pytest.mark.parametrize(
    ('base_url', 'pid', 'expected'),
    [
        (
            'https://dataverse.example.com',
            'doi:10.1234/example',
            'https://dataverse.example.com/dataset.xhtml?persistentId=doi%3A10.1234%2Fexample',
        ),
        (
            'https://dataverse.example.com/',
            'doi:10.5678/test',
            'https://dataverse.example.com/dataset.xhtml?persistentId=doi%3A10.5678%2Ftest',
        ),
        (
            'http://localhost:8080',
            'hdl:12345/ABC',
            'http://localhost:8080/dataset.xhtml?persistentId=hdl%3A12345%2FABC',
        ),
        (
            'https://demo.dataverse.org/',
            'doi:10.70122/FK2/ABCDEF',
            'https://demo.dataverse.org/dataset.xhtml?persistentId=doi%3A10.70122%2FFK2%2FABCDEF',
        ),
    ],
)
def test_parse_dataset_url_valid(base_url, pid, expected):
    """Test parse_dataset_url with valid inputs."""
    result = parse_dataset_url(base_url, pid)
    assert result == expected


def test_parse_dataset_url_none_base_url():
    """Test parse_dataset_url with None base_url."""
    result = parse_dataset_url(None, 'doi:10.1234/example')
    assert result == 'No URL'


def test_parse_dataset_url_none_pid():
    """Test parse_dataset_url with None pid."""
    result = parse_dataset_url('https://dataverse.example.com', None)
    assert result == 'No URL'


def test_parse_dataset_url_both_none():
    """Test parse_dataset_url with both parameters None."""
    result = parse_dataset_url(None, None)
    assert result == 'No URL'


def test_parse_dataset_url_empty_strings():
    """Test parse_dataset_url with empty strings."""
    result = parse_dataset_url('', '')
    assert result == 'No URL'


def test_parse_dataset_url_special_characters():
    """Test parse_dataset_url properly encodes special characters in PID."""
    base_url = 'https://dataverse.example.com'
    pid = 'doi:10.1234/test/data set'
    result = parse_dataset_url(base_url, pid)
    # Space should be encoded as %20, forward slashes as %2F, colon as %3A
    assert (
        'persistentId=doi%3A10.1234%2Ftest%2Fdata+set' in result
        or 'persistentId=doi%3A10.1234%2Ftest%2Fdata%20set' in result
    )
