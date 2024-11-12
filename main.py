# pylint: disable=C0114, C0301, C0116
import os
import shutil
import sys
import typer
import dotenv
import pydatacuration.utils as utils
import pydatacuration.downloads as downloads
import pydatacuration.checksum as checksum
import pydatacuration.directory_manager as directory_manager
import pydatacuration.files_opener as files_opener
import pydatacuration.template_generation as template_generation
import pydatacuration.spell_checker as spell_checker
import pydatacuration.metadata_checker as metadata_checker

app = typer.Typer()

# TODO: Change this to a class and return the value, and put it to the default value of the main function
def load_env(base_url, api_token):
    dotenv.load_dotenv()
    if base_url is None:
        base_url = os.getenv('BASE_URL')
        if base_url is None:
            sys.exit('BASE_URL not found in the environment variables. Exiting...')
    if api_token is None:
        api_token = os.getenv('API_TOKEN')
        if api_token is None:
            sys.exit('API_TOKEN not found in the environment variables. Exiting...')
    print('Environment variables loaded')
    return base_url, api_token


def workdir_manager():
    if os.path.exists('workdir'):
        shutil.rmtree('workdir')
    workdir = os.path.join(os.getcwd(), 'workdir')
    dm = directory_manager.DirectoryManager(workdir)
    dm.mk_log_dir()
    dm.mk_ds_dir()
    dm.mk_temp_dir()
    print('\nWorkdir created')
    return workdir

def parse_file_list_metadata(file_list_metadata):
    file_list_metadata_nested_list = []
    for file_meta in file_list_metadata:
        filename = file_meta.get('dataFile', {}).get('originalFileName') or file_meta.get('dataFile', {}).get('filename')
        directory_label = file_meta.get('directoryLabel', '')
        file_full_path = os.path.join(directory_label, filename)
        file_list_metadata_nested_list.append({
            'file': file_full_path,
            'md5_checksum': file_meta['dataFile']['md5']
        })

    return file_list_metadata_nested_list


def download_files(base_url, api_token, doi, workdir):
    download = downloads.Downloads(base_url, api_token, doi, workdir)

    # Initiating the downloads
    print('\nDownloading dataset metadata...')
    ds_metadata = download.get_ds_metadata()
    print('Dataset metadata downloaded\n')

    # Download the dataset as a zip file using the 'Basic Download By Dataset' API
    print('\nDownloading dataset in zip format...')
    ds_zip_path = download.get_ds_zip()
    print('Dataset in zip format downloaded\n')
    # Unzip the file and move the MANIFEST file to the 'dataset/metadata' directory
    utils.unzip_file(ds_zip_path, f'{os.path.join(workdir, "dataset", "files")}')

    # Check the checksum of the downloaded files
    checksums = checksum.Checksum()

    dl_file_checksum_nested_list = checksums.gen_ds_files_checksum(os.path.join(workdir, 'dataset', 'files/'))

    file_list_metadata = ds_metadata['data']['latestVersion']['files']


    file_list_metadata_nested_list = parse_file_list_metadata(file_list_metadata)

    utils.compare_files_and_metadata(dl_file_checksum_nested_list, file_list_metadata_nested_list, workdir)

    return file_list_metadata

def checker(file_list_metadata):
    template_dict = template_generation.read_template_json()

    def _check_file_name_format(file_list_metadata, template_dict: dict):

        file_name_format_checker = utils.FileNameFormatChecker()
        for file in file_list_metadata:
            file_datafile_filename = file.get('dataFile', {}).get('originalFileName') or file.get('dataFile', {}).get('filename')

            if file_name_format_checker.check_special_char(file_datafile_filename)[1] is True:
                print('\n')
                print(f"Special characters found in the filename: {file_datafile_filename}")
                template_dict['special_characters']['comments'].append({"file_name": file_datafile_filename})

            if file_name_format_checker.check_file_name_len(file_datafile_filename, 32)[1] is True:
                print('\n')
                print(f"Filename is longer than 32 characters: {file_datafile_filename}")
                template_dict['long_file_length']['comments'].append({"file_name": file_datafile_filename})

            if file_name_format_checker.check_file_ext(file_datafile_filename)[1] is True:
                print('\n')
                print(f"File extension does not found: {file_datafile_filename}")
                template_dict['file_ext']['comments'].append({"file_name": file_datafile_filename})

            if utils.readme_file_checker(file_datafile_filename)[1] is True:
                print('\n')
                print(f"README file found: {file_datafile_filename}")
                template_dict['readme_file']['comments'].append({"file_name": file_datafile_filename})

        file_list = []
        for item in file_list_metadata:
            file_name = item.get('dataFile', {}).get('originalFileName') or item.get('dataFile', {}).get('filename')
            file_list.append(os.path.join("./workdir/dataset/files", item.get('directoryLabel', ''), file_name))

        for file in file_list:
            if files_opener.FilesOpener(file).open_file()[0] is False:
                print(f"\nFile cannot be opened: {file}")
                template_dict['file_open']['comments'].append({"file_name": file})
            elif files_opener.FilesOpener(file).open_file()[0] is None:
                print(f'\nFile is not a supported file format (not checked by the script): {file}')
                template_dict['file_open']['not_checked'].append({"file_name": file})

        return template_dict

    def _check_missing_metadata(template_dict: dict):
        mc = metadata_checker.MetadataChecker('./workdir/dataset/metadata/ds_metadata.json')

        field_list = ['title', 'dsDescription', 'subject']
        for field in field_list:
            return_value = mc.check_metadata_cm_field(field)
            if return_value[1] is False:
                print(f"\nMissing metadata found in the {field}")
                template_dict['missing_field'][field]['comments'].append(f'Missing metadata in {field} field')

        field_list_author = ['authorAffiliation', 'authorIdentifierScheme', 'authorIdentifier']
        result = mc.check_author_cm_field()
        for item in result:
            author_name = item.get('authorName')
            for field in field_list_author:
                if item.get(field) is None:
                    print(f"\nMissing metadata found in {field} field for author: {author_name}")
                    template_dict['missing_field'][field]['comments'].append(f'Missing metadata in {field} field for author: {author_name}')

        return template_dict

    def _check_spelling(template_dict: dict):
        sc = spell_checker.SpellCheckerCustomized()
        mc = metadata_checker.MetadataChecker('./workdir/dataset/metadata/ds_metadata.json')

        field_list = ['title', 'subtitle', 'alternativeTitle', 'dsDescription.dsDescriptionValue', 'notesText']
        for field in field_list:
            return_value, field_exists = mc.check_metadata_cm_field(field)

            if field_exists:
                typos, has_typos = sc.check_spelling(return_value[0])
                if has_typos:
                    typo_messages = [f"Typo found in {field}: `{item}`" for item in typos]
                    for message in typo_messages:
                        print(f"\nSpelling mistake found in the {field}: {message}")
                    template_dict['typo']['comments'].extend(typo_messages)

        return template_dict

    template_dict_new = _check_file_name_format(file_list_metadata, template_dict)
    template_dict_new = _check_missing_metadata(template_dict_new)
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
                                  prompt = '\nEnter the API token',
                                  envvar='API_TOKEN')
):

    base_url, api_token = load_env(base_url, api_token)
    workdir = workdir_manager()
    file_list_metadata = download_files(base_url, api_token, doi, workdir)
    template_dict = checker(file_list_metadata)
    template_generation.generate_report(template_dict)

if __name__ == "__main__":
    app()
