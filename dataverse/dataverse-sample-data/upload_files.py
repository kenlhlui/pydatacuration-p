from pathlib import Path

import dvconfig
import dvuploader as dv


# Create a dataset in the Toronto dataverse using the API client and metadata JSON file
base_url = dvconfig.base_url
api_token = dvconfig.api_token


# Upload the data files
dataset_pid = 'doi:10.80240/FK2/TDW1J7'  # FIXME: don't use hardcoded PID, get it from the create_dataset.py script

# Get the list of file paths from the dataverse/dataverse-sample-data/data/dataverses/toronto/datasets/toronto/files directory

files_dir = Path('./data/dataverses/toronto/datasets/toronto/files')

files_dir.glob('*')
print(list(files_dir.glob('*')))

files = [*dv.add_directory(Path('./data/dataverses/toronto/datasets/toronto/files'))]
dvuploader = dv.DVUploader(files=files)

dvuploader.upload(
    api_token=api_token,
    dataverse_url=base_url,
    persistent_id=dataset_pid,
    n_parallel_uploads=2,  # Whatever your instance can handle
)
