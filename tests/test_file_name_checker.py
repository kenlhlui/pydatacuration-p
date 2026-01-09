"""Test the file_name_checker.py module."""

import pytest
from loguru import logger

from pydatacuration.checker.file_name_checker import FileNameFormatChecker


@pytest.mark.parametrize(
    ('input_string', 'expected_bool'),
    [
        ('test_file.txt', False),
        ('test-file.txt', False),
        ('test file.txt', False),
        ('test@file.txt', True),
        ('test$file.txt', True),
        ('test,file.txt', True),
        ('test<file.txt', True),
        ('test>file.txt', True),
        ('test:file.txt', True),
        ('test"file.txt', True),
        ('test|file.txt', True),
        ('test?file.txt', True),
        ('test*file.txt', True),
        ('test~file.txt', True),
        ('test\rfile.txt', True),
        ('test\nfile.txt', True),
        ('path/to/file.txt', False),
        ('path/to/bad@file.txt', True),
    ],
)
def test_check_special_chars(input_string, expected_bool):
    """Test for special character checking function."""
    result_file, result_bool = FileNameFormatChecker.check_special_char(input_string)
    assert result_file == input_string
    assert result_bool is expected_bool


@pytest.mark.parametrize(
    ('input_string', 'expected_bool'),
    [
        ('s.txt', False),
        ('veryveryverylongfilename.txt', True),
    ],
)
def test_check_file_name_len(input_string, expected_bool):
    FILE_NAME_MAX_LEN = 10  # noqa: N806
    result_file, result_bool = FileNameFormatChecker.check_file_name_len(input_string, FILE_NAME_MAX_LEN)
    assert result_file == input_string
    assert result_bool is expected_bool


@pytest.mark.parametrize(
    ('input_string', 'expected_bool'),
    [
        ('document.pdf', False),
        ('image.jpeg', False),
        ('archive.zip', False),
        ('.py', True),
        ('no_extension', True),
        ('file.with.many.dots.txt', False),
    ],
)
def test_check_file_ext(input_string, expected_bool):
    """Test for file extension checking function."""
    result_file, result_bool = FileNameFormatChecker.check_file_ext(input_string)
    assert result_file == input_string
    assert result_bool is expected_bool


def test_check_file_preferred_format(tmp_path):
    """Test for checking preferred file formats."""
    # Create a temporary config file
    config_content = '.txt\n.csv\n.md'
    config_file = tmp_path / 'preferred_formats.txt'
    config_file.write_text(config_content, encoding='utf-8')
    config_path = str(config_file)

    # Test with a preferred format
    file_valid = 'example.txt'
    result_file, result_bool = FileNameFormatChecker.check_file_preferred_format(file_valid, config_path)
    assert result_file == file_valid
    assert result_bool is True

    # Test with a non-preferred format
    file_invalid = 'example.jpg'
    result_file, result_bool = FileNameFormatChecker.check_file_preferred_format(file_invalid, config_path)
    assert result_file == file_invalid
    assert result_bool is False


def test_check_file_preferred_format_missing_config():
    """Test behavior when config file is missing."""
    with pytest.raises(SystemExit):
        FileNameFormatChecker.check_file_preferred_format('test.txt', 'non_existent_file.txt')
