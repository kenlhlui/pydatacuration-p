# pylint: disable=C0114, C0301, C0116
import os
import shutil
import typer
import dotenv
import orjson
from jinja2 import Environment, FileSystemLoader, Template
import pydatacuration.utils as utils
import pydatacuration.downloads as downloads
import pydatacuration.checksum as checksum
import pydatacuration.directory_manager as directory_manager
import pandas as pd


app = typer.Typer()

@app.command()
def load_env():
    dotenv.load_dotenv()
    BASE_URL = os.getenv('BASE_URL')
    API_TOKEN = os.getenv('API_TOKEN')
    print('Environment variables loaded')
    return BASE_URL, API_TOKEN

@app.command()
def ask_user_doi():
    doi = typer.prompt('\nEnter DOI')
    return doi

@app.command()
def workdir_manager():
    workdir = os.path.join(os.getcwd(), 'workdir')
    shutil.rmtree('workdir')
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

@app.command()
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

def read_template_json():
    with open('./res/template.json', 'r') as file:
        template = orjson.loads(file.read())
    return template

def FileNameFormatChecker(file_list_metadata):
    FileNameFormatChecker = utils.FileNameFormatChecker()

    template_dict = read_template_json()

    for file in file_list_metadata:
        if FileNameFormatChecker.check_special_char(file['dataFile']['filename'])[1] == True:
            print('\n')
            print(f"Special characters found in the filename: {file['dataFile']['filename']}")
            template_dict['special_characters']['status'] = {"SI": "X"}
            template_dict['special_characters']['comments'].append({"file_name": file['dataFile']['filename']})
        else:
            if not template_dict['special_characters']['status']:
                template_dict['special_characters']['status'] = {"Y": "X"}

    for file in file_list_metadata:
        if FileNameFormatChecker.check_file_name_len(file['dataFile']['filename'], 32)[1] == True:
            print('\n')
            print(f"Filename is longer than 32 character: {file['dataFile']['filename']}")
            template_dict['long_file_length']['status'] = {"SI": "X"}
            template_dict['long_file_length']['comments'].append({"file_name": file['dataFile']['filename']})
        else:
            template_dict['long_file_length']['status'] = {"Y": "X"}
    

    return template_dict

@app.command()
def generate_report(template_dict):
    def read_csv_template(file):
        with open(file, 'r', encoding='ISO-8859-1') as f:
            content = f.read()
        return content
    
    template_string = read_csv_template('./res/template.csv')
    report = Template(template_string)
    rendered = report.render(template_dict=template_dict)
    with open('./workdir/log_files/temp_data/render_log.csv', 'w', encoding='utf-8') as f:
        f.write(rendered)
    pd.read_csv('./workdir/log_files/temp_data/render_log.csv').to_excel('./workdir/log_files/render_log.xlsx', index=False)

def main():
    base_url, url = load_env()
    doi = ask_user_doi()
    workdir = workdir_manager()
    file_list_metadata = download_files(base_url, url, doi, workdir)
    template_dict = FileNameFormatChecker(file_list_metadata)
    generate_report(template_dict)
    print('\nReport generated. See the workdir/log_files/render_log.xlsx file for the report.')

if __name__ == "__main__":
    main()