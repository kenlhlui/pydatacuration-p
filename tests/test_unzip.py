from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from pydatacuration.unzip import Unzipper


@pytest.mark.parametrize(
    ('zip_file_name'),
    [
        ('zip_file.zip'),
    ],
)
def test_main_unzips_and_returns_extracted_paths(tmp_path: Path, zip_file_name: str) -> None:
    """main extracts a zip and returns paths to extracted files.

    Args:
        tmp_path (Path): Temporary directory provided by pytest.

    Returns:
        None: This test does not return anything.

    """
    zip_path = tmp_path / zip_file_name
    out_dir = tmp_path / 'out'

    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr('a.txt', 'hello')
        zf.writestr('nested/b.txt', 'world')

    unzipper = Unzipper(zip_path, out_dir)

    extracted = unzipper.main()

    assert (out_dir / 'a.txt').exists()
    assert (out_dir / 'nested' / 'b.txt').exists()
