"""The checker module provides functions to check the validity of data files and metadata."""

from pathlib import Path

import httpx
import jmespath
import yaml

from .checksum import Checksum
from .custom_logging import CustomLogger
from .files_opener import FilesOpener
from .log_generation import GenerateLog
from .metadata_checker import MetadataChecker
from .spell_checker import SpellCheckerCustomized
from .utils import FileNameFormatChecker
from .utils import compare_files_and_metadata
from .utils import parse_file_list_metadata
from .utils import readme_file_checker


RES_DIR = Path('res')


class Checker:
    """Checker class to validate the data files and metadata."""
    def __init__(self,
                 base_url: str,
                 api_token: str,
                 ds_metadata: dict,
                 workdir: Path) -> None:
        """Initialize the Checker class.

        Args:
            base_url (str): The base URL of the API.
            api_token (str): The API token"
            ds_metadata (dict): The dataset metadata.
            workdir (Path): The working directory.
        """
        self.base_url = base_url
        self.api_token = api_token
        self.ds_metadata = ds_metadata
        self.workdir = workdir

        self.logger = CustomLogger.get_logger(__name__)
        self.checksums = Checksum()
        self.template_dict = GenerateLog.read_template_json()
        self.files_opener = FilesOpener
        self.metadata_checker = MetadataChecker(self.workdir.joinpath('dataset', 'metadata', 'ds_metadata.json'))
        self.spell_checker = SpellCheckerCustomized()
        self.file_list_metadata = self._gen_file_list_metadata()
        self.common_file_format_tuple = self._read_common_file_format()

    def _read_common_file_format(self) -> tuple | None:
        """Reads the common_file_format.yaml file and returns it as a dictionary.

        Returns:
            dict: The common file format as a dictionary.
        """
        try:
            # Check if the file exists
            if RES_DIR.joinpath('common_file_formats.yaml').exists():
                # Open the file and read its content
                with RES_DIR.joinpath('common_file_formats.yaml').open(encoding='utf-8') as file:
                    common_file_format_dict = yaml.safe_load(file)

                    file_formats = set()
                    for _category, extensions in common_file_format_dict['file_formats'].items():
                        file_formats.update(extensions)  # Use set to avoid duplicates

                    return tuple(file_formats)  # Convert set to tuple for immutability

        except FileNotFoundError:
            # Handle the case where the file is not found
            self.logger.error('common_file_formats.yaml file not found in the res directory.')
            return None

    def _gen_file_list_metadata(self) -> list:
        """Generate the file list metadata.

        Returns:
            list: The file list metadata.
        """
        # Check the checksum of the downloaded files
        dl_file_checksum_nested_list = self.checksums.gen_ds_files_checksum(self.workdir)

        file_list_metadata = self.ds_metadata['data']['latestVersion']['files']

        file_list_metadata_nested_list = parse_file_list_metadata(file_list_metadata)

        compare_files_and_metadata(dl_file_checksum_nested_list, file_list_metadata_nested_list, self.workdir)

        return file_list_metadata

    def check_file_name_format(self) -> None:
        """Check the file name format."""
        file_name_format_checker = FileNameFormatChecker()
        for file in self.file_list_metadata:
            file_name = file.get('dataFile', {}).get('originalFileName') or file.get('dataFile', {}).get('filename')
            file_rel_path = Path(file.get('directoryLabel', ''), file_name)

            if file_name_format_checker.check_special_char(file_name)[1] is True:
                self.logger.print(f'Special characters found in the filename: {file_rel_path}')
                self.template_dict['special_characters']['comments'].append({'file_name': str(file_rel_path)})

            if file_name_format_checker.check_file_ext(file_name)[1] is True:
                self.logger.print(f'File extension does not found: {file_rel_path}')
                self.template_dict['file_ext']['comments'].append({'file_name': str(file_rel_path)})

            if readme_file_checker(file_name)[1] is True:
                self.logger.print(f'README file found: {file_rel_path}')
                self.template_dict['readme_file']['comments'].append({'file_name': str(file_rel_path)})

        file_list = []

        for file in self.file_list_metadata:
            file_name = file.get('dataFile', {}).get('originalFileName') or file.get('dataFile', {}).get('filename')
            file_rel_path = Path(file.get('directoryLabel', ''), file_name)
            file_list.append(file_rel_path)

        for file_rel_path in file_list:
            file_abs_path = Path(self.workdir, 'dataset', 'files', file_rel_path)
            if self.files_opener(file_abs_path).open_file()[0] is False:
                self.logger.print(f'File cannot be opened: {file_abs_path}')
                self.template_dict['file_open']['comments'].append({'file_name': str(file_rel_path)})
            elif self.files_opener(file_abs_path).open_file()[0] is None:
                self.logger.print(f'File is not a supported file format (not checked by the script): {file_abs_path}')
                self.template_dict['file_open']['not_checked'].append({'file_name': str(file_rel_path)})

    def check_common_file_format(self) -> None:
        """Check if the file format is in the common file format."""
        if self.common_file_format_tuple:
            for file in self.file_list_metadata:
                file_name = file.get('dataFile', {}).get('originalFileName') or file.get('dataFile', {}).get('filename')
                file_rel_path = Path(file.get('directoryLabel', ''), file_name)
                file_abs_path = Path(self.workdir, 'dataset', 'files', file_rel_path)
                file_ext = file_rel_path.suffix
                if file_ext.startswith('.') and file_ext not in self.common_file_format_tuple:
                    self.logger.print(f'File is not a common file format: {file_abs_path}')
                    self.template_dict['common_file_format']['comments'].append({'file_name': str(file_rel_path)})
        else:
            self.logger.error('No common file format found in the res directory. Skipping this check.')
            self.template_dict['common_file_format']['comments'].append('No common file format found in the res directory. Skipping this check.')  # noqa: E501

    def check_missing_metadata(self) -> None:
        """Check for missing metadata."""
        field_list = ['title', 'dsDescription', 'subject']
        for field in field_list:
            return_value = self.metadata_checker.check_metadata_cm_field(field)
            if return_value[1] is False:
                self.logger.print(f'Missing metadata found in the {field}')
                self.template_dict['missing_field'][field]['comments'].append(f'Missing metadata in {field} field')

        # Check any associated fields for an author (affiliation, identifier & scheme) are missing
        field_list_author = ['authorAffiliation', 'authorIdentifierScheme', 'authorIdentifier']
        author_info_dict = self.metadata_checker.check_author_cm_field()
        for item in author_info_dict:
            author_name = item.get('authorName')
            for field in field_list_author:
                if item.get(field) is None:
                    self.logger.print(f'Missing metadata found in {field} field for author: {author_name}')
                    self.template_dict['missing_field'][field]['comments'].append(f'Missing metadata in {field} field for author: {author_name}')  # noqa: E501

        # Check if at least one author has authorAffiliation
        author_affiliation_num = len([item for item in author_info_dict if item.get('authorAffiliation') is not None])
        if author_affiliation_num == 0:
            self.logger.print('None of the authors have an institutional affiliation listed')
            self.template_dict['none_author_affiliation'] = True

    def check_spelling(self) -> None:
        """Check for spelling mistakes in the metadata."""
        field_list = ['title', 'subtitle', 'alternativeTitle', 'dsDescription.dsDescriptionValue', 'notesText']
        for field in field_list:
            return_value, field_exists = self.metadata_checker.check_metadata_cm_field(field)

            if field_exists:
                typos, has_typos = self.spell_checker.check_spelling(return_value[0])
                if has_typos:
                    typo_messages = [f'{field}: `{item}`' for item in typos]
                    for message in typo_messages:
                        self.logger.print(f'Spelling mistake found in the {field}: {message}')
                    self.template_dict['typo']['comments'].extend(typo_messages)

    def check_dv_record(self) -> None:
        """Check if the author has a Dataverse record."""
        query_string = 'data.latestVersion.metadataBlocks.citation.fields[?typeName==`author`].value[*].authorName.value[]'  # noqa: E501
        author_list = jmespath.search(query_string, self.ds_metadata)

        if isinstance(author_list, list):
            for author in author_list:
                # Remove all non-alphanumeric characters from the author name
                author = ''.join(char for char in author if char.isalpha() or char.isspace())
                # Check if the author has record by search API
                response = httpx.get(f'{self.base_url}/api/search?q={author}&type=dataset&per_page=100',
                                      headers={'X-Dataverse-key': self.api_token})
                if response.status_code == 200 and response.json():
                    name_of_dataverse_result = list(set(jmespath.search('data.items[*].name_of_dataverse', response.json())))  # noqa: E501
                    self.template_dict['dv_record']['comments'].append({author: name_of_dataverse_result})

    def check_dv_collection(self) -> None:
        """Check if the dataset is in a Dataverse collection."""
        ds_version_id = self.ds_metadata.get('data', {}).get('latestVersion', {}).get('id')
        if ds_version_id:
            # See https://github.com/IQSS/dataverse/issues/2038 for fq field;
            # Also check the source code the the available fq fields https://github.com/IQSS/dataverse/blob/develop/src/main/java/edu/harvard/iq/dataverse/search/SearchFields.java
            # Use 'datasetVersionId' here; in ds_metadata it is data.latestVersion.id
            # Don't mess up with data.id or data.latestVersion.datasetId which are the same and is the persistent id in the dataverse system  # noqa: E501
            response = httpx.get(f'{self.base_url}/api/search?q=*&type=dataset&per_page=1&fq=datasetVersionId:{ds_version_id}',  # noqa: E501
                                 headers={'X-Dataverse-key': self.api_token})
            if response.status_code == 200 and response.json():
                name_of_dataverse = response.json().get('data', {}).get('items', [{}])[0].get('name_of_dataverse', None)
                self.template_dict['name_of_dataverse'] = name_of_dataverse

    def check_restricted_files(self) -> None:
        """Check for restricted files."""
        for item in self.file_list_metadata:
            if item.get('restricted') is True:
                file_name = item.get('dataFile', {}).get('originalFileName') or item.get('dataFile', {}).get('filename')
                file_path = Path(item.get('directoryLabel', ''), file_name)
                print(f'Restricted file found: {file_path}')
                self.template_dict['restricted_files']['comments'].append({'file_name': str(file_path)})

    def check_terms_license(self) -> None:
        """Check if the terms of use and license are present."""
        terms_of_use = self.ds_metadata.get('data', {}).get('latestVersion', {}).get('termsOfUse', None)
        terms_of_access = self.ds_metadata.get('data', {}).get('latestVersion', {}).get('termsOfAccess', None)
        license_name = self.ds_metadata.get('data', {}).get('latestVersion', {}).get('license', {}).get('name', None)

        self.template_dict['terms_license']['termsOfUse'] = terms_of_use
        self.template_dict['terms_license']['termsOfAccess'] = terms_of_access
        self.template_dict['terms_license']['licenseName'] = license_name

        if license_name == 'CC0 1.0':
            self.logger.print('The license is CC0 1.0')

        if len(self.template_dict['restricted_files']['comments']) > 0 and \
            (terms_of_use is None or terms_of_access is None):
            self.logger.print('The terms of use and access are missing')

    def run_checks(self) -> dict:
        """Run all the checks."""
        self.check_file_name_format()
        self.check_common_file_format()
        self.check_missing_metadata()
        self.check_spelling()
        self.check_dv_record()
        self.check_dv_collection()
        self.check_restricted_files()
        self.check_terms_license()

        return self.template_dict
