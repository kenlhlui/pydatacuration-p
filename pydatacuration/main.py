#!/usr/bin/env python3
"""The main module of the pydatacuration CLI application."""
# ruff: noqa: E501, W505
import asyncio
import os
from pathlib import Path
from typing import Optional

import httpx
import jmespath
import orjson
import typer
from dotenv import load_dotenv
from trogon.typer import init_tui
from typing_extensions import Annotated

from . import checksum
from . import directory_manager
from . import downloads
from . import files_opener
from . import log_generation
from . import metadata_checker
from . import spell_checker
from . import utils


# Load environment variables from .env file
load_dotenv(override=True)


app = typer.Typer()
init_tui(app)


def gen_file_list_metadata(workdir: Path, ds_metadata: dict) -> list:
    """Generate the file list metadata.

    Args:
        workdir (Path): The working directory.
        ds_metadata (dict): The dataset metadata.

    Returns:
        list: The file list metadata.
    """
    # Check the checksum of the downloaded files
    checksums = checksum.Checksum()

    dl_file_checksum_nested_list = checksums.gen_ds_files_checksum(workdir)

    file_list_metadata = ds_metadata['data']['latestVersion']['files']

    file_list_metadata_nested_list = utils.parse_file_list_metadata(file_list_metadata)

    utils.compare_files_and_metadata(dl_file_checksum_nested_list, file_list_metadata_nested_list, workdir)

    return file_list_metadata


def checker(base_url: str, api_token: str, ds_metadata: dict, file_list_metadata: list, workdir: Path) -> dict:
    template_dict = log_generation.GenerateLog.read_template_json()

    def _check_file_name_format(file_list_metadata: list, template_dict: dict):

        file_name_format_checker = utils.FileNameFormatChecker()
        for file in file_list_metadata:
            file_datafile_filename = file.get('dataFile', {}).get('originalFileName') or file.get('dataFile', {}).get('filename')

            if file_name_format_checker.check_special_char(file_datafile_filename)[1] is True:
                print('\n')
                print(f'Special characters found in the filename: {file_datafile_filename}')
                template_dict['special_characters']['comments'].append({'file_name': str(file_datafile_filename)})

            if file_name_format_checker.check_file_ext(file_datafile_filename)[1] is True:
                print('\n')
                print(f'File extension does not found: {file_datafile_filename}')
                template_dict['file_ext']['comments'].append({'file_name': str(file_datafile_filename)})

            if utils.readme_file_checker(file_datafile_filename)[1] is True:
                print('\n')
                print(f'README file found: {file_datafile_filename}')
                template_dict['readme_file']['comments'].append({'file_name': str(file_datafile_filename)})

        file_list = []
        for item in file_list_metadata:
            file_name = item.get('dataFile', {}).get('originalFileName') or item.get('dataFile', {}).get('filename')
            file_path = Path(workdir, 'dataset', 'files', item.get('directoryLabel', ''), file_name)
            file_list.append(file_path)

        for file in file_list:
            if files_opener.FilesOpener(file).open_file()[0] is False:
                print(f'\nFile cannot be opened: {file}')
                template_dict['file_open']['comments'].append({'file_name': str(file)})
            elif files_opener.FilesOpener(file).open_file()[0] is None:
                print(f'\nFile is not a supported file format (not checked by the script): {file}')
                template_dict['file_open']['not_checked'].append({'file_name': str(file)})

        return template_dict

    def _check_missing_metadata(template_dict: dict, workdir: Path) -> dict:
        mc = metadata_checker.MetadataChecker(workdir.joinpath('dataset', 'metadata', 'ds_metadata.json'))

        field_list = ['title', 'dsDescription', 'subject']
        for field in field_list:
            return_value = mc.check_metadata_cm_field(field)
            if return_value[1] is False:
                print(f'\nMissing metadata found in the {field}')
                template_dict['missing_field'][field]['comments'].append(f'Missing metadata in {field} field')

        # Check any associated fields for an author (affiliation, identifier & scheme) are missing
        field_list_author = ['authorAffiliation', 'authorIdentifierScheme', 'authorIdentifier']
        author_info_dict = mc.check_author_cm_field()
        for item in author_info_dict:
            author_name = item.get('authorName')
            for field in field_list_author:
                if item.get(field) is None:
                    print(f'\nMissing metadata found in {field} field for author: {author_name}')
                    template_dict['missing_field'][field]['comments'].append(f'Missing metadata in {field} field for author: {author_name}')

        # Check if at least one author has authorAffiliation
        author_affiliation_num = len([item for item in author_info_dict if item.get('authorAffiliation') is not None])
        if author_affiliation_num == 0:
            print('\nNone of the authors have an institutional affiliation listed')
            template_dict['none_author_affiliation'] = True

        return template_dict

    def _check_spelling(template_dict: dict) -> dict:
        sc = spell_checker.SpellCheckerCustomized()
        mc = metadata_checker.MetadataChecker(Path(workdir, 'dataset', 'metadata', 'ds_metadata.json'))

        field_list = ['title', 'subtitle', 'alternativeTitle', 'dsDescription.dsDescriptionValue', 'notesText']
        for field in field_list:
            return_value, field_exists = mc.check_metadata_cm_field(field)

            if field_exists:
                typos, has_typos = sc.check_spelling(return_value[0])
                if has_typos:
                    typo_messages = [f'{field}: `{item}`' for item in typos]
                    for message in typo_messages:
                        print(f'\nSpelling mistake found in the {field}: {message}')
                    template_dict['typo']['comments'].extend(typo_messages)

        return template_dict

    def _check_dv_record(template_dict: dict) -> dict:
        query_string = 'data.latestVersion.metadataBlocks.citation.fields[?typeName==`author`].value[*].authorName.value[]'
        author_list = jmespath.search(query_string, ds_metadata)

        dv_list = []
        if isinstance(author_list, list):
            for author in author_list:
                # Remove all non-alphanumeric characters from the author name
                author = ''.join(char for char in author if char.isalpha() or char.isspace())
                # Check if the author has record by search API
                response = httpx.get(f'{base_url}/api/search?q={author}&type=dataset&per_page=100', headers={'X-Dataverse-key': api_token})
                if response.status_code == 200 and response.json():
                    name_of_dataverse_result = list(set(jmespath.search('data.items[*].name_of_dataverse', response.json())))
                    template_dict['dv_record']['comments'].append({author: name_of_dataverse_result})

        return template_dict

    def _check_dv_collection(template_dict: dict) -> dict:
        ds_version_id = ds_metadata.get('data', {}).get('latestVersion', {}).get('id')
        if ds_version_id:
            # See https://github.com/IQSS/dataverse/issues/2038 for fq field;
            # Also check the source code the the available fq fields https://github.com/IQSS/dataverse/blob/366d7ac6907a405421fe1ebdaad21b636e3b74f7/src/main/java/edu/harvard/iq/dataverse/search/SearchFields.java#L4
            # Use 'datasetVersionId' here; in ds_metadata it is data.latestVersion.id
            # Don't mess up with data.id or data.latestVersion.datasetId which are the same and is the persistent id in the dataverse system
            response = httpx.get(f'{base_url}/api/search?q=*&type=dataset&per_page=1&fq=datasetVersionId:{ds_version_id}',
                                 headers={'X-Dataverse-key': api_token})
            if response.status_code == 200 and response.json():
                name_of_dataverse = response.json().get('data', {}).get('items', [{}])[0].get('name_of_dataverse', None)
                template_dict['name_of_dataverse'] = name_of_dataverse

        return template_dict

    def _check_restricted_files(file_list_metadata: list, template_dict: dict) -> dict:
        # Check and return file path if restricted
        for item in file_list_metadata:
            if item.get('restricted') is True:
                file_name = item.get('dataFile', {}).get('originalFileName') or item.get('dataFile', {}).get('filename')
                file_path = Path(item.get('directoryLabel', ''), file_name)
                print(f'\nRestricted file found: {file_path}')
                template_dict['restricted_files']['comments'].append({'file_name': str(file_path)})

        return template_dict

    def _check_terms_license(template_dict: dict) -> dict:
        # Check if the terms of use and license are present
        terms_of_use = ds_metadata.get('data', {}).get('latestVersion', {}).get('termsOfUse', None)
        terms_of_access = ds_metadata.get('data', {}).get('latestVersion', {}).get('termsOfAccess', None)
        license_name = ds_metadata.get('data', {}).get('latestVersion', {}).get('license', {}).get('name', None)

        template_dict['terms_license']['termsOfUse'] = terms_of_use
        template_dict['terms_license']['termsOfAccess'] = terms_of_access
        template_dict['terms_license']['licenseName'] = license_name

        if license_name == 'CC0 1.0':
            print('\n The license is CC0 1.0')

        if len(template_dict['restricted_files']['comments']) > 0 and (terms_of_use is None or terms_of_access is None):
            print('\n The terms of use and access are missing')

        return template_dict

    template_dict_new = _check_file_name_format(file_list_metadata, template_dict)
    template_dict_new = _check_missing_metadata(template_dict_new, workdir)
    template_dict_new = _check_spelling(template_dict_new)
    template_dict_new = _check_dv_record(template_dict_new)
    template_dict_new = _check_dv_collection(template_dict_new)
    template_dict_new = _check_restricted_files(file_list_metadata, template_dict_new)
    template_dict_new = _check_terms_license(template_dict_new)

    return template_dict_new


@app.command()
def main(

    doi: str = typer.Option(None,
                            prompt=('Input the Dataset Persistent Identifier (doi or hdl)'),
                            help='Enter the Persistent Identifier of the dataset'),
    base_url: str = typer.Option(None,
                                 help='The base URL of the Dataverse installation',
                                 prompt=('Input the base URL of the Dataverse installation'),
                                 prompt_required=True,
                                 envvar='BASE_URL'),
    api_token: str = typer.Option(None,
                                  help='The API token for the Dataverse installation',
                                  prompt=('Input the API token for the Dataverse installation'),
                                  hide_input=True,
                                  prompt_required=True,
                                  envvar='API_TOKEN'),
    parent_dir: str = typer.Option('workdir',
                                help='The working directory. If not specified, a directory "workdir" will be created in the current directory',
                                show_default=True,
                                ),
    ticket_number: str = typer.Option(None,
                                      help='The ticket number for the curation report; Also the directory name created under the working directory',
                                      prompt=('Input the ticket number for the curation report'),
                                      prompt_required=True,
                                      callback=utils.check_ticket_num_input,
                                      )) -> None:
    """This script downloads the dataset files and metadata from a Dataverse instance and checks the files and metadata for data curation, and generates a curation report in spreadsheet (.xlsx) and world (.docx) format."""  # noqa: E501, W505
    workdir_path, log_files_dir, ds_dir, temp_data_dir = directory_manager.DirectoryManager(ticket_number, parent_dir).make_dirs()
    ds_metadata = asyncio.run(downloads.Downloads(base_url, api_token, doi, workdir_path).downloader())
    file_list_metadata = gen_file_list_metadata(workdir_path, ds_metadata)
    template_dict = checker(base_url, api_token, ds_metadata, file_list_metadata, workdir_path)

    # Generate the report
    generate_log = log_generation.GenerateLog(workdir_path, base_url, ds_metadata, ticket_number)
    generate_log.generate_report_xlsx(template_dict)
    generate_log.generate_report_doc(template_dict)
    generate_log.generate_project_metadata()

    # Export the template dict to JSON for debugging purposes
    with temp_data_dir.joinpath('template_dict.json').open('w') as f:
        f.write(orjson.dumps(template_dict, option=orjson.OPT_INDENT_2).decode())

    utils.gen_tree_diagram(Path(workdir_path, 'dataset', 'files'), Path(log_files_dir))

    # Print the end message
    print(f'\n✅ Curation report generated successfully. \n\nType (or copy) the following (without quotes) in the terminal to view the files: \n\n`explorer.exe {workdir_path}`')

if __name__ == '__main__':
    app()
