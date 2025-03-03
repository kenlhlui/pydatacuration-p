# ruff: noqa: E501, W505
import asyncio
import os
from pathlib import Path

import checksum
import directory_manager
import downloads
import files_opener
import metadata_checker
import spell_checker
import template_generation
import typer
import utils


app = typer.Typer()


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

def checker(file_list_metadata, workdir: Path) -> dict:
    template_dict = template_generation.read_template_json()

    def _check_file_name_format(file_list_metadata, template_dict: dict):

        file_name_format_checker = utils.FileNameFormatChecker()
        for file in file_list_metadata:
            file_datafile_filename = file.get('dataFile', {}).get('originalFileName') or file.get('dataFile', {}).get('filename')

            if file_name_format_checker.check_special_char(file_datafile_filename)[1] is True:
                print('\n')
                print(f'Special characters found in the filename: {file_datafile_filename}')
                template_dict['special_characters']['comments'].append({'file_name': file_datafile_filename})

            if file_name_format_checker.check_file_ext(file_datafile_filename)[1] is True:
                print('\n')
                print(f'File extension does not found: {file_datafile_filename}')
                template_dict['file_ext']['comments'].append({'file_name': file_datafile_filename})

            if utils.readme_file_checker(file_datafile_filename)[1] is True:
                print('\n')
                print(f'README file found: {file_datafile_filename}')
                template_dict['readme_file']['comments'].append({'file_name': file_datafile_filename})

        file_list = []
        for item in file_list_metadata:
            file_name = item.get('dataFile', {}).get('originalFileName') or item.get('dataFile', {}).get('filename')
            file_path = Path(workdir, 'dataset', 'files', item.get('directoryLabel', ''), file_name)
            file_list.append(file_path)

        for file in file_list:
            if files_opener.FilesOpener(file).open_file()[0] is False:
                print(f'\nFile cannot be opened: {file}')
                template_dict['file_open']['comments'].append({'file_name': file})
            elif files_opener.FilesOpener(file).open_file()[0] is None:
                print(f'\nFile is not a supported file format (not checked by the script): {file}')
                template_dict['file_open']['not_checked'].append({'file_name': file})

        return template_dict

    def _check_missing_metadata(template_dict: dict, workdir: Path) -> dict:
        mc = metadata_checker.MetadataChecker(workdir.joinpath('dataset', 'metadata', 'ds_metadata.json'))

        field_list = ['title', 'dsDescription', 'subject']
        for field in field_list:
            return_value = mc.check_metadata_cm_field(field)
            if return_value[1] is False:
                print(f'\nMissing metadata found in the {field}')
                template_dict['missing_field'][field]['comments'].append(f'Missing metadata in {field} field')

        field_list_author = ['authorAffiliation', 'authorIdentifierScheme', 'authorIdentifier']
        result = mc.check_author_cm_field()
        for item in result:
            author_name = item.get('authorName')
            for field in field_list_author:
                if item.get(field) is None:
                    print(f'\nMissing metadata found in {field} field for author: {author_name}')
                    template_dict['missing_field'][field]['comments'].append(f'Missing metadata in {field} field for author: {author_name}')

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
                    typo_messages = [f'Typo found in {field}: `{item}`' for item in typos]
                    for message in typo_messages:
                        print(f'\nSpelling mistake found in the {field}: {message}')
                    template_dict['typo']['comments'].extend(typo_messages)

        return template_dict

    template_dict_new = _check_file_name_format(file_list_metadata, template_dict)
    template_dict_new = _check_missing_metadata(template_dict_new, workdir)
    template_dict_new = _check_spelling(template_dict_new)

    return template_dict_new


@app.command()
def main(

    doi: str = typer.Option(None, prompt=('Input the Dataset Persistent Identifier (doi or hdl)'), help='Enter the Persistent Identifier of the dataset'),
    base_url: str = typer.Option(None,
                                 help='The base URL of the Dataverse installation',
                                 envvar='BASE_URL'),
    api_token: str = typer.Option(None,
                                  help='The API token for the Dataverse installation',
                                  hide_input=True,
                                  prompt='\nEnter the API token',
                                  envvar='API_TOKEN'),
    workdir: str = typer.Option('workdir',
                                help='The working directory'
                                )) -> None:
    """This script downloads the dataset files and metadata from a Dataverse instance and checks the files and metadata for data curation, and generates a curation report in spreadsheet (.xlsx) format."""  # noqa: E501, W505
    base_url, api_token = utils.load_env(base_url, api_token)
    workdir, log_files_dir, ds_dir, temp_data_dir = directory_manager.DirectoryManager(workdir).make_dirs()
    ds_metadata = asyncio.run(downloads.Downloads(base_url, api_token, doi, workdir).downloader())

    file_list_metadata = gen_file_list_metadata(workdir, ds_metadata)
    template_dict = checker(file_list_metadata, workdir)
    template_generation.generate_report(template_dict, workdir)
    utils.gen_tree_diagram(Path(workdir, 'dataset', 'files'), Path(log_files_dir))

if __name__ == "__main__":
    app()
