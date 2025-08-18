"""The checker module provides functions to check the validity of data files and metadata."""

from pathlib import Path

import jmespath
import yaml

from .checksum import Checksum
from .custom_logging import CustomLogger
from .files_opener import FilesOpener
from .httpx_client import HTTPXClient
from .log_generation import GenerateLog
from .metadata_checker import MetadataChecker
from .spell_checker import SpellCheckerCustomized
from .unzip import Unzipper
from .utils import FileNameFormatChecker
from .utils import compare_files_and_metadata
from .utils import parse_file_list_metadata
from .utils import readme_file_checker


RES_DIR = Path('res')


class CheckResultBuilder:
    """Builder class for collecting check results in a structured format."""

    def __init__(self) -> None:
        """Initialize the CheckResultBuilder."""
        self.results = []

    def add_check_result(self, check_id: str, check_name: str,
                         description: str, result_name: str, results: list, allow_empty: bool = False) -> None:
        """Add a check result to the collection.

        Args:
            check_id (str): Unique identifier for the check
            check_name (str): Human-readable name of the check
            description (str): Description of what the check finds
            result_name (str): Name of the result (value, file, keyword, etc)
            results (list): List of findings from the check
            allow_empty (bool): Whether to allow empty results
        """
        # Only add if there are actual results
        if results or allow_empty:
            self.results.append({
                'check_id': check_id,
                'check_name': check_name,
                'description': description,
                'result_type': result_name,
                'results': results
            })

    def get_results(self) -> list:
        """Get all collected check results."""
        return self.results


class Checker:
    """Checker class to validate the data files and metadata."""
    def __init__(self,
                 base_url: str,
                 api_token: str,
                 ds_metadata: dict,
                 dv_tree: dict,
                 workdir: Path,
                 check_zip: bool,
                 collection_alias: str | None = None) -> None:
        """Initialize the Checker class.

        Args:
            base_url (str): The base URL of the API.
            api_token (str): The API token"
            ds_metadata (dict): The dataset metadata.
            dv_tree (dict): The Dataverse tree metadata.
            workdir (Path): The working directory.
            check_zip (bool): Whether to check zip files.
            collection_alias (str | None): The collection alias for the author name to be searched.
        """
        self.base_url = base_url
        self.api_token = api_token
        self.ds_metadata = ds_metadata
        self.dv_tree = dv_tree
        self.workdir = workdir
        self.check_zip = check_zip
        self.collection_alias = collection_alias

        self.logger = CustomLogger.get_logger(__name__)
        self.checksums = Checksum()
        self.template_dict = GenerateLog.read_template_json()
        self.result_builder = CheckResultBuilder()
        self.files_opener = FilesOpener
        self.metadata_checker = MetadataChecker(self.workdir.joinpath('dataset', 'metadata', 'ds_metadata.json'))
        self.spell_checker = SpellCheckerCustomized()
        self.httpx_client = HTTPXClient(base_url, api_token)
        self.file_list_metadata = self._gen_file_list_metadata()
        self.common_file_format_tuple = self._read_common_file_format()

        self.ds_title = jmespath.search('data.latestVersion.metadataBlocks.citation.fields[?typeName == `title`].value | [0]', self.ds_metadata)  # ! Temp fix; should use log_generation.py _get_dataset_info to get the title.  # noqa

    def _get_ds_tree_info(self, identifier_of_dataverse: str) -> dict:
        """Get the dataset tree information in the Dataverse repository.

        Args:
            identifier_of_dataverse(str): The identifier of the dataverse parent dataverse.

        Returns:
            dict: A dictionary containing the path to the target node, empty if none.
        """
        def _process(data: dict, id_list: list, alias_list: list, name_list: list) -> dict:
            # Append the current node's alias and name to the respective lists
            # Create new lists with current node's information
            current_id_list = id_list + [data.get('id')]
            current_alias_list = alias_list + [data.get('alias')]
            current_name_list = name_list + [data.get('name')]

            # Check if the current node is the target
            if data.get('alias') == identifier_of_dataverse:
                result = {
                    'id': current_id_list,
                    'alias': current_alias_list,
                    'depth': data.get('depth'),
                    'name': current_name_list
                }
                # Combine the paths with '/' separator
                result['path'] = '/'.join(current_name_list)
                # Turn the id, alias and name from list to tuple
                result['id'] = tuple(result['id'])
                result['alias'] = tuple(result['alias'])
                result['name'] = tuple(result['name'])
                return result

            # Recursively search through any children
            for child in data.get('children', []):
                result = _process(child, current_id_list, current_alias_list, current_name_list)
                if result:  # This is correct - if a non-empty result is returned from any child, pass it up
                    return result  # Return the result immediately when found

            # If we get here, no match was found in this branch
            return {}

        # Read the root node from the JSON once
        root = self.dv_tree.get('data', {}) if self.dv_tree.get('status') == 'OK' else {}
        result = _process(root, [], [], [])
        return result

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
        special_char_files = []
        missing_ext_files = []
        readme_files = []
        
        for file in self.file_list_metadata:
            file_name = file.get('dataFile', {}).get('originalFileName') or file.get('dataFile', {}).get('filename')
            file_rel_path = Path(file.get('directoryLabel', ''), file_name)

            if file_name_format_checker.check_special_char(file_name)[1] is True:
                self.logger.print(f'Special characters found in the filename: {file_rel_path}')
                self.template_dict['special_characters']['comments'].append({'file_name': str(file_rel_path)})
                special_char_files.append(str(file_rel_path))

            if file_name_format_checker.check_file_ext(file_name)[1] is True:
                self.logger.print(f'File extension does not found: {file_rel_path}')
                self.template_dict['file_ext']['comments'].append({'file_name': str(file_rel_path)})
                missing_ext_files.append(str(file_rel_path))

            if readme_file_checker(file_name)[1] is True:
                self.logger.print(f'README file found: {file_rel_path}')
                self.template_dict['readme_file']['comments'].append({'file_name': str(file_rel_path)})
                readme_files.append(str(file_rel_path))

        # Add results to the new structure
        self.result_builder.add_check_result(
            check_id='filename_special_chars',
            check_name='Files with Special Characters',
            description='Files containing special characters in filename',
            result_name='file',
            results=special_char_files
        )

        self.result_builder.add_check_result(
            check_id='missing_file_extensions',
            check_name='Files Missing Extensions',
            description='Files without proper file extensions',
            result_name='file',
            results=missing_ext_files
        )

        self.result_builder.add_check_result(
            check_id='readme_files',
            check_name='README Files Found',
            description='README files detected in the dataset',
            result_name='file',
            results=readme_files
        )

    def check_file_open(self) -> None:
        """Check if the file can be opened."""
        file_list = []
        inaccessible_files = []
        unsupported_files = []

        # To generate paths for the relative files in the dataset
        for file in self.file_list_metadata:
            file_name = file.get('dataFile', {}).get('originalFileName') or file.get('dataFile', {}).get('filename')
            file_rel_path = Path(file.get('directoryLabel', ''), file_name)
            file_list.append(file_rel_path)

        # Unzip the files and append the unzipped files to the file_list
        zip_file_extensions = {'.tar', '.tar.gz', '.tar.bz2', '.tar.xz', '.gz', '.bz2', '.xz', '.7z', '.zip'}
        if self.check_zip:
            for file_rel_path in file_list[:]:  # Iterate over a copy of the list
                if file_rel_path.suffix in zip_file_extensions:
                    # Upper case the suffix and remove the leading dot
                    extracted_file_rel_paths = Unzipper(
                        zip_file=Path(self.workdir, 'dataset', 'files', file_rel_path),
                        output_dir=Path(self.workdir, 'dataset', 'files', '__UNZIPED_FILES__', f'{file_rel_path.stem}_{file_rel_path.suffix[1:].upper()}')
                    ).main()
                    file_list.extend(extracted_file_rel_paths)
        # Only show the message if there's zip file(s) in the dataset
        elif not self.check_zip and any(file_rel_path.suffix in zip_file_extensions for file_rel_path in file_list):
            self.logger.print('Skipping the unzipping of zip file(s). The zip file(s) and the content inside will not be checked.')  # noqa: E501

        for file_rel_path in file_list:
            file_abs_path = Path(self.workdir, 'dataset', 'files', file_rel_path)
            # Pass if the file is a zip file
            if file_rel_path.suffix not in zip_file_extensions:
                if self.files_opener(file_abs_path).open_file()[0] is False:
                    self.logger.print(f'File cannot be opened: {file_abs_path}')
                    self.template_dict['file_open']['comments'].append({'file_name': str(file_rel_path)})
                    inaccessible_files.append(str(file_rel_path))
                elif self.files_opener(file_abs_path).open_file()[0] is None:
                    self.logger.print(f'File is not a supported file format (not checked by the script): {file_abs_path}')  # noqa: E501
                    self.template_dict['file_open']['not_checked'].append({'file_name': str(file_rel_path)})
                    unsupported_files.append(str(file_rel_path))

        # Add results to the new structure
        self.result_builder.add_check_result(
            check_id='file_accessibility',
            check_name='Inaccessible Files',
            description='Files that cannot be opened or read by the validation tool',
            result_name='file',
            results=inaccessible_files
        )

        self.result_builder.add_check_result(
            check_id='unsupported_files',
            check_name='Files with Unsupported Formats',
            description='Files in formats not supported by the validation tool',
            result_name='file',
            results=unsupported_files
        )

    def check_common_file_format(self) -> None:
        """Check if the file format is in the common file format."""
        uncommon_format_files = []

        if self.common_file_format_tuple:
            for file in self.file_list_metadata:
                file_name = file.get('dataFile', {}).get('originalFileName') or file.get('dataFile', {}).get('filename')
                file_rel_path = Path(file.get('directoryLabel', ''), file_name)
                file_abs_path = Path(self.workdir, 'dataset', 'files', file_rel_path)
                file_ext = file_rel_path.suffix
                if file_ext.startswith('.') and file_ext not in self.common_file_format_tuple:
                    self.logger.print(f'File is not a common file format: {file_abs_path}')
                    self.template_dict['common_file_format']['comments'].append({'file_name': str(file_rel_path)})
                    uncommon_format_files.append(str(file_rel_path))
        else:
            self.logger.error('No common file format found in the res directory. Skipping this check.')
            self.template_dict['common_file_format']['comments'].append('No common file format found in the res directory. Skipping this check.')  # noqa: E501

        # Add results to the new structure
        self.result_builder.add_check_result(
            check_id='uncommon_file_formats',
            check_name='Files with Uncommon Formats',
            description='Files using uncommon or proprietary file formats',
            result_name='file',
            results=uncommon_format_files
        )

    def check_missing_metadata(self) -> None:
        """Check for missing metadata."""
        missing_required_fields = []
        authors_missing_affiliation = []
        authors_missing_identifier = []
        authors_missing_scheme = []

        field_list = ['title', 'dsDescription', 'subject']
        for field in field_list:
            return_value = self.metadata_checker.check_metadata_cm_field(field)
            if return_value[1] is False:
                self.logger.print(f'Missing metadata found in the {field}')
                self.template_dict['missing_field'][field]['comments'].append(f'Missing metadata in {field} field')
                missing_required_fields.append(field)

        # Check any associated fields for an author (affiliation, identifier & scheme) are missing
        field_list_author = ['authorAffiliation', 'authorIdentifierScheme', 'authorIdentifier']
        author_info_dict = self.metadata_checker.check_author_cm_field()
        for item in author_info_dict:
            author_name = item.get('authorName')
            for field in field_list_author:
                if item.get(field) is None:
                    self.logger.print(f'Missing metadata found in {field} field for author: {author_name}')
                    self.template_dict['missing_field'][field]['comments'].append(f'{author_name}')  # noqa: E501

                    # Collect authors missing specific fields
                    if field == 'authorAffiliation':
                        authors_missing_affiliation.append(author_name)
                    elif field == 'authorIdentifier':
                        authors_missing_identifier.append(author_name)
                    elif field == 'authorIdentifierScheme':
                        authors_missing_scheme.append(author_name)

        # Check if at least one author has authorAffiliation
        author_affiliation_num = len([item for item in author_info_dict if item.get('authorAffiliation') is not None])
        if author_affiliation_num == 0:
            self.logger.print('None of the authors have an institutional affiliation listed')
            self.template_dict['none_author_affiliation'] = True

        # Check if at least one author has affiliation with 'University of Toronto' (Non-case sensitive)
        ut_variants = ['university of toronto', 'uoft', 'u of t']
        author_affiliation_ut_num = len([item for item in author_info_dict if item.get('authorAffiliation') is not None and any(variant in item.get('authorAffiliation', '').lower() for variant in ut_variants)])  # noqa: E501
        if author_affiliation_ut_num == 0:
            self.logger.print('None of the authors have listed affiliation with University of Toronto')
            self.template_dict['none_author_affiliation_UT'] = True

        # Add results to the new structure
        self.result_builder.add_check_result(
            check_id='missing_required_fields',
            check_name='Missing Required Metadata Fields',
            description='Required metadata fields that are empty or missing',
            result_name='file',
            results=missing_required_fields
        )

        self.result_builder.add_check_result(
            check_id='authors_missing_affiliation',
            check_name='Authors Without Affiliation',
            description='Authors missing institutional affiliation information',
            result_name='author',
            results=authors_missing_affiliation
        )

        self.result_builder.add_check_result(
            check_id='authors_missing_identifier',
            check_name='Authors Without Identifier',
            description='Authors missing personal identifier (ORCID, etc.)',
            result_name='author',
            results=authors_missing_identifier
        )

        self.result_builder.add_check_result(
            check_id='authors_missing_scheme',
            check_name='Authors Without Identifier Scheme',
            description='Authors missing identifier scheme information',
            result_name='author',
            results=authors_missing_scheme
        )

    def check_spelling(self) -> None:
        """Check for spelling mistakes in the metadata."""
        potential_typos = []
        
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

                    # Collect typos for new structure
                    for typo in typos:
                        potential_typos.append({
                            'field': field,
                            'typo': typo,
                            'context': return_value[0][:100] + '...' if len(return_value[0]) > 100 else return_value[0]
                        })

        # Add results to the new structure
        self.result_builder.add_check_result(
            check_id='potential_typos',
            check_name='Potential Spelling Errors',
            description='Words that may contain spelling mistakes in metadata fields',
            result_name='typo',
            results=potential_typos
        )

    def check_dv_record(self) -> None:
        """Check if the author has deposited data in Dataverse.

        Note: This check only works if the author inputs their name in a consistent way across all datasets.

        """
        author_publication_history = []

        query_string = 'data.latestVersion.metadataBlocks.citation.fields[?typeName==`author`].value[*].authorName.value[]'  # noqa: E501
        author_list = jmespath.search(query_string, self.ds_metadata)

        if isinstance(author_list, list):
            for author in author_list:
                # Check if the author has record by search API
                # See https://github.com/IQSS/dataverse/issues/2038 for fq field;
                # Note that fq supports searching the fields of the database schema
                # i.e. The fields in the Native JSON export of a dataset
                if self.collection_alias:
                    response = self.httpx_client.sync_get(f'/api/search?q=*&type=dataset&per_page=1000&subtree={self.collection_alias}&fq=authorName:"{author}"')  # noqa: E501
                else:
                    # If no collection_alias is provided, search in all dataverses
                    response = self.httpx_client.sync_get(f'/api/search?q=*&type=dataset&per_page=1000&fq=authorName:"{author}"')  # noqa: E501
                if response and response.json():
                    name_of_dataverse_result = list(set(jmespath.search('data.items[*].name_of_dataverse', response.json())))  # noqa: E501
                    dataset_titles = jmespath.search('data.items[*].name', response.json()) or []

                    self.template_dict['dv_record']['comments'].append({author: name_of_dataverse_result})

                    # Collect for new structure
                    author_publication_history.append({
                        'author': author,
                        'datasets': dataset_titles,
                        'dataverses': name_of_dataverse_result
                    })

                # TODO: Add error handling for the case when the response is None or empty; or HTTP error

        # Add results to the new structure
        self.result_builder.add_check_result(
            check_id='author_dataverse_history',
            check_name='Author Publication History',
            description='Previous datasets published by authors in this Dataverse instance',
            result_name='author history',
            results=author_publication_history
        )

    def check_ds_tree_info(self) -> None:
        """Check the path of the dataset in the dataverse Repository."""
        ds_version_id = self.ds_metadata.get('data', {}).get('latestVersion', {}).get('id')
        if ds_version_id:
            # See https://github.com/IQSS/dataverse/issues/2038 for fq field;
            # Also check the source code the the available fq fields https://github.com/IQSS/dataverse/blob/develop/src/main/java/edu/harvard/iq/dataverse/search/SearchFields.java
            # Use 'datasetVersionId' here; in ds_metadata it is data.latestVersion.id
            # Don't mess up with data.id or data.latestVersion.datasetId which are the same and is the persistent id in the dataverse system  # noqa: E501
            response = self.httpx_client.sync_get(f'/api/search?q=*&type=dataset&per_page=1&fq=datasetVersionId:{ds_version_id}')  # noqa: E501
            if response and response.json():
                # Get the name_of_dataverse from the response
                name_of_dataverse = response.json().get('data', {}).get('items', [{}])[0].get('name_of_dataverse', None)  # noqa: E501
                if name_of_dataverse:
                    self.template_dict['ds_tree_info']['parentDataverseName'] = name_of_dataverse

                # Get the path of the dataverse from the response
                identifier_of_dataverse = response.json().get('data', {}).get('items', [{}])[0].get('identifier_of_dataverse', None)  # noqa: E501
                tree_info = self._get_ds_tree_info(identifier_of_dataverse)
                path: str | None = tree_info.get('path', None)
                if path:
                    # Add the dataset title to the end of the path
                    ds_title = self.ds_title if self.ds_title else 'Unknown Dataset Title'
                    # Join the Path
                    self.template_dict['ds_tree_info']['path'] = f'{path}/{ds_title}'
                    self.logger.debug(f'Dataset path in the dataverse repository: {self.template_dict["ds_tree_info"]["path"]}')  # noqa: E501

                # Add the result to self.result_builder
                self.result_builder.add_check_result(
                    check_id='dataset_path',
                    check_name='Dataset Path Information',
                    description="Information about the dataset's location in the Dataverse repository",
                    result_name='dataset_path',
                    results=[self.template_dict['ds_tree_info']['path']]
                )

            # TODO: Add error handling for the case when the response is None or empty; or HTTP error

    def check_restricted_files(self) -> None:
        """Check for restricted files."""
        restricted_files = []

        for item in self.file_list_metadata:
            if item.get('restricted') is True:
                file_name = item.get('dataFile', {}).get('originalFileName') or item.get('dataFile', {}).get('filename')
                file_path = Path(item.get('directoryLabel', ''), file_name)
                self.logger.print(f'Restricted file found: {file_path}')
                self.template_dict['restricted_files']['comments'].append({'file_name': str(file_path)})
                restricted_files.append(str(file_path))

        # Add results to the new structure
        self.result_builder.add_check_result(
            check_id='restricted_files',
            check_name='Restricted Access Files',
            description='Files with access restrictions in the dataset',
            result_name='file',
            results=restricted_files
        )

    def check_terms_of_use(self) -> None:
        """Check if the terms of use are present."""
        terms_of_use = self.ds_metadata.get('data', {}).get('latestVersion', {}).get('termsOfUse', None)
        self.template_dict['terms_license']['termsOfUse'] = terms_of_use

        # Add results to the new structure
        self.result_builder.add_check_result(
            check_id='termsOfUse',
            check_name='Terms of Use of the Dataset',
            description='Terms of Use information in the dataset',
            result_name='terms of use',
            results=[
                terms_of_use,
            ]
        )

    def check_terms_of_access(self) -> None:
        """Check if the terms of access are present."""
        terms_of_access = self.ds_metadata.get('data', {}).get('latestVersion', {}).get('termsOfAccess', None)
        self.template_dict['terms_license']['termsOfAccess'] = terms_of_access

        # Add results to the new structure
        self.result_builder.add_check_result(
            check_id='termsOfAccess',
            check_name='Terms of Access of the Dataset',
            description='Terms of Access information in the dataset',
            result_name='term of access',
            results=[
                terms_of_access,
            ]
        )

    def check_license(self) -> None:
        """Check if the terms of use and license are present."""
        license_name = self.ds_metadata.get('data', {}).get('latestVersion', {}).get('license', {}).get('name', None)

        self.template_dict['terms_license']['licenseName'] = license_name

        self.result_builder.add_check_result(
            check_id='license',
            check_name='License of the Dataset',
            description='License information in the dataset',
            result_name='license',
            results=[
                license_name,
            ]
        )

        if license_name == 'CC0 1.0':
            self.logger.print('The license is CC0 1.0')

    def check_keywords(self) -> None:
        """Check if the keywords are present."""
        query_string = 'data.latestVersion.metadataBlocks.citation.fields[?typeName==`keyword`].value[*].keywordValue.value[]'  # noqa: E501
        keyword_list = jmespath.search(query_string, self.ds_metadata)
        if isinstance(keyword_list, list):
            self.template_dict['keywords'] = keyword_list
            self.logger.print(f'Keywords found in the metadata: {keyword_list}')

        # Add the result to self.result_builder
        self.result_builder.add_check_result(
            check_id='keywords_existence',
            check_name='Keywords Existence',
            description='Check if keywords are present in the dataset',
            result_name='keyword',
            results=keyword_list,
            allow_empty=True
        )

    def run_checks(self) -> tuple[dict, dict]:
        """Run all the checks.

        Returns:
            tuple: (template_dict for backward compatibility, new check_results structure)
        """
        self.logger.print('Running the checks...')
        self.check_file_name_format()
        self.check_file_open()
        self.check_common_file_format()
        self.check_missing_metadata()
        self.check_spelling()
        self.check_dv_record()
        self.check_ds_tree_info()
        self.check_restricted_files()
        self.check_terms_of_use()
        self.check_terms_of_access()
        self.check_keywords()
        self.check_license()

        # Build the new structure
        new_results = {
            'check_results': self.result_builder.get_results()
        }

        return self.template_dict, new_results
