"""End-to-end: curate the seeded sample dataset on a live Dataverse and check the per-file results.

Skipped unless E2E_BASE_URL, E2E_API_TOKEN and E2E_PID are set (see tests/README.md). In CI these come from
.github/workflows/e2e.yml after tests/e2e/seed_dataverse.py uploads tests/e2e/sample_data/.
"""

import os
from pathlib import Path

import pytest


pytestmark = pytest.mark.skipif(
    not all(os.environ.get(var) for var in ('E2E_BASE_URL', 'E2E_API_TOKEN', 'E2E_PID')),
    reason='E2E_BASE_URL, E2E_API_TOKEN and E2E_PID must be set to run against a Dataverse instance',
)

SAMPLE_FILES_DIR = Path(__file__).parent / 'sample_data' / 'files'
SAMPLE_FILES = sorted(p.relative_to(SAMPLE_FILES_DIR).as_posix() for p in SAMPLE_FILES_DIR.rglob('*') if p.is_file())

CHECK_IDS = [
    'authors_missing_affiliation',
    'authors_missing_identifier',
    'authors_missing_scheme',
    'data_sources_entries',
    'depositor_history',
    'file_openability',
    'filename_special_chars',
    'keywords_existence',
    'license',
    'missing_file_extensions',
    'missing_required_fields',
    'potential_typos',
    'readme_files',
    'related_datasets_entries',
    'related_publications_entries',
    'restricted_files',
    'termsOfAccess',
    'termsOfUse',
    'uncommon_file_formats',
    'unsupported_files',
]

BROKEN_FILES = [
    'audio/sample_mp3_audio.corrupted.mp3',
    'nc/broken.nc',
    'pdf/borken_pdf.pdf',
    'rdata/borken.RData',
    'spreadsheet/spreadsheet_normal_broken.xlsx',
    'tif/original - borken.tif',
]

VALID_FILES = [
    'audio/sample_mp3_audio.mp3',
    'nc/normal.nc',
    'pdf/normal_pdf.pdf',
    'rdata/normal.RData',
    'spreadsheet/spreadsheet_normal.xlsx',
    'test_folder/this_is_a_xlsx_file.xlsx',
    'tif/original.tif',
    'tsv_file.tsv',
]

RESTRICTED_FILES = [
    'restricted/restricted_file.txt',
    'restricted/restricted_file_without_terms.txt',
]


@pytest.mark.parametrize('rel_path', SAMPLE_FILES)
def test_should_download_every_sample_file(curated_project, rel_path):
    # Arrange
    downloaded = curated_project.dirs.files_dir / rel_path

    # Act / Assert
    assert downloaded.is_file()


@pytest.mark.parametrize('check_id', CHECK_IDS)
def test_should_write_result_for_every_check(curated_project, check_id):
    # Arrange
    written_check_ids = curated_project.results.keys()

    # Act / Assert
    assert check_id in written_check_ids


@pytest.mark.parametrize('rel_path', BROKEN_FILES)
def test_should_flag_broken_file_as_unopenable(curated_project, rel_path):
    # Arrange
    unopenable = curated_project.results['file_openability']

    # Act / Assert
    assert rel_path in unopenable


@pytest.mark.parametrize('rel_path', VALID_FILES)
def test_should_open_valid_file(curated_project, rel_path):
    # Arrange
    unopenable = curated_project.results['file_openability']

    # Act / Assert
    assert rel_path not in unopenable


def test_should_report_unsupported_extension(curated_project):
    # Arrange
    unsupported = curated_project.results['unsupported_files']

    # Act / Assert
    assert 'unspported file/sub_dir/unsupported_ext.est' in unsupported


@pytest.mark.parametrize('rel_path', RESTRICTED_FILES)
def test_should_list_restricted_file(curated_project, rel_path):
    # Arrange
    restricted = curated_project.results['restricted_files']

    # Act / Assert
    assert rel_path in restricted


def test_should_flag_special_character_filename(curated_project):
    # Arrange
    special_char_files = curated_project.results['filename_special_chars']

    # Act / Assert
    assert 'special_char/~filewithspecialchar.txt' in special_char_files


def test_should_find_readme(curated_project):
    # Arrange
    readme_files = curated_project.results['readme_files']

    # Act / Assert
    assert 'Chapeter 1/README' in readme_files


def test_should_flag_missing_extension(curated_project):
    # Arrange
    missing_ext_files = curated_project.results['missing_file_extensions']

    # Act / Assert
    assert 'Chapeter 1/README' in missing_ext_files


def test_should_extract_zip_contents(curated_project):
    # Arrange
    extracted_dir = curated_project.dirs.files_dir / '__UNZIPED_FILES__' / 'png_in_a_zip_file_ZIP'

    # Act
    extracted_pngs = list(extracted_dir.rglob('*.png'))

    # Assert
    assert extracted_pngs


def test_should_export_word_report(curated_project):
    # Arrange
    report = curated_project.dirs.outputs_dir / 'curation_report.docx'

    # Act / Assert
    assert report.is_file()
