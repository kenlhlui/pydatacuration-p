import json
from pathlib import Path

import dvconfig
import dvuploader as dv
from pyDataverse.api import NativeApi


# Create a dataset in the Toronto dataverse using the API client and metadata JSON file
base_url = dvconfig.base_url
api_token = dvconfig.api_token

# Create the API client
native_api = NativeApi(base_url, api_token)

# Load the dataset metadata from the JSON file
dataset_json = 'data/dataverses/toronto/datasets/toronto/toronto.json'
with Path(dataset_json).open(encoding='utf-8') as f:
    metadata = json.load(f)

# The dataverse alias where the dataset will be created
dataverse = 'toronto'

# Create the dataset
resp = native_api.create_dataset(
    dataverse,
    metadata=json.dumps(metadata),
    pid='doi:10.80240/FK2/FCZB4A',
    publish=False,
)
print(resp)

# Upload the data files
dataset_pid = resp.json()['data']['persistentId']

# Get the list of file paths from the files directory

files_dir = Path('./dataverse/dataverse-sample-data/data/dataverses/toronto/datasets/toronto/files')

files = [*dv.add_directory(Path('./data/dataverses/toronto/datasets/toronto/files'))]

# Create the DVUploader instance and upload the files
dvuploader = dv.DVUploader(files=files)

dvuploader.upload(
    api_token=api_token,
    dataverse_url=base_url,
    persistent_id=dataset_pid,
    n_parallel_uploads=2,  # Whatever your instance can handle
)

print('Dataset created and files uploaded successfully!')
