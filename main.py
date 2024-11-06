# pylint: disable=C0114, C0301, C0116
import os
import shutil
import typer
import dotenv
import orjson
from jinja2 import Template
import pandas as pd
import pydatacuration.utils as utils
import pydatacuration.downloads as downloads
import pydatacuration.checksum as checksum
import pydatacuration.directory_manager as directory_manager
import pydatacuration.files_opener as files_opener
import pydatacuration.template_generation as template_generation

app = typer.Typer()

def load_env():
    dotenv.load_dotenv()
    base_url = os.getenv('BASE_URL')
    api_token = os.getenv('API_TOKEN')
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
        if file_meta.get('directoryLabel'):
            file_list_metadata_nested_list.append({
                'file': f"{file_meta['directoryLabel']}/{file_meta['dataFile']['filename']}",
                'md5_checksum': file_meta['dataFile']['md5']
            })
        else:
            file_list_metadata_nested_list.append({
                'file': file_meta['dataFile']['filename'],
                'md5_checksum': file_meta['dataFile']['md5']
            })

    return file_list_metadata_nested_list


def download_files(base_url, api_token, doi, workdir):
    download = downloads.Downloads(base_url, api_token, doi, workdir)

    # Initiating the downloads
    ds_metadata = download.get_ds_metadata()
    print('\nDataset metadata downloaded')

    # Download the dataset as a zip file using the 'Basic Download By Dataset' API
    ds_zip_path = download.get_ds_zip()
    print('\nDataset in zip format downloaded')
    # Unzip the file and move the MANIFEST file to the 'dataset/metadata' directory
    utils.unzip_file(ds_zip_path, f'{os.path.join(workdir, "dataset", "files")}')

    # Check the checksum of the downloaded files
    checksums = checksum.Checksum()

    dl_file_checksum_nested_list = checksums.gen_ds_files_checksum(os.path.join(workdir, 'dataset', 'files/'))

    file_list_metadata = ds_metadata['data']['latestVersion']['files']


    file_list_metadata_nested_list = parse_file_list_metadata(file_list_metadata)

    utils.compare_files_and_metadata(dl_file_checksum_nested_list, file_list_metadata_nested_list, workdir)

    return file_list_metadata

def file_name_format_checker(file_list_metadata):
    file_name_format_checker = utils.FileNameFormatChecker()

    template_dict = template_generation.read_template_json()


    for file in file_list_metadata:
        file_datafile_filename = file.get('dataFile').get('filename')

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
        file_list.append(os.path.join("./workdir/dataset/files", item.get('directoryLabel', ''), item.get('dataFile').get('filename')))

    for file in file_list:
        if files_opener.FilesOpener(file).open_file()[0] is False:
            print(f"\nFile cannot be opened: {file}")
            template_dict['file_open']['comments'].append({"file_name": file})
        elif files_opener.FilesOpener(file).open_file()[0] is None:
            print(f'\nFile is not a supported file: {file}')
            template_dict['file_open']['not_checked'].append({"file_name": file})

    # for key, value in template_dict.items():
    #     if not template_dict[key]['status']: # FIXME: Not to use 'status' anymore
    #         template_dict[key]['status'] = {"NA": "X"}

    return template_dict

@app.command()
def main(
    doi: str = typer.Option(None, prompt=('Input the Dataset Persistent Identifier (doi or hdl)'), help='Enter the Persistent Identifier of the dataset')
):

    base_url, api_token = load_env()
    workdir = workdir_manager()
    file_list_metadata = download_files(base_url, api_token, doi, workdir)
    template_dict = file_name_format_checker(file_list_metadata)
    template_generation.generate_report(template_dict)

if __name__ == "__main__":
    app()
