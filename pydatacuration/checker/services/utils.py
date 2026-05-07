"""Utility functions for the checker module."""

from pathlib import Path


def get_file_name_from_file_list_metadata(file_list_metadata: dict) -> str:
    """Get the file name from the file list metadata.

    Args:
        file_list_metadata (list[dict]): The file list metadata.

    Returns:
        str: The file name.
    """
    file_name = file_list_metadata.get('dataFile', {}).get('originalFileName') or file_list_metadata.get(
        'dataFile', {}
    ).get('filename')

    return file_name


def get_file_rel_path_from_file_list_metadata(file_list_metadata: dict, file_name: str) -> Path:
    """Get the file relative path from the file list metadata.

    Args:
        file_list_metadata (list[dict]): The file list metadata.
        file_name (str): The file name.

    Returns:
        Path: The file relative path object.
    """
    return Path(file_list_metadata.get('directoryLabel', ''), file_name)
