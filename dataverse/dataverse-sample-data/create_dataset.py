import json
from pathlib import Path

import dvconfig
import dvuploader as dv
from pyDataverse.api import Api


# Create a dataset in the Toronto dataverse using the API client and metadata JSON file
base_url = dvconfig.base_url
api_token = dvconfig.api_token
api = Api(base_url, api_token)
print(api.status)
dataset_json = 'data/dataverses/toronto/datasets/toronto/toronto.json'
with open(dataset_json) as f:
    metadata = json.load(f)
dataverse = 'toronto'
resp = api.create_dataset(dataverse, json.dumps(metadata))
print(resp)


# Upload the data files
dataset_pid = resp.json()['data']['persistentId']

# Get the list of file paths from the dataverse/dataverse-sample-data/data/dataverses/toronto/datasets/toronto/files directory

files_dir = Path('./dataverse/dataverse-sample-data/data/dataverses/toronto/datasets/toronto/files')

files = [*dv.add_directory(Path('./data/dataverses/toronto/datasets/toronto/files'))]
dvuploader = dv.DVUploader(files=files)

dvuploader.upload(
    api_token=api_token,
    dataverse_url=base_url,
    persistent_id=dataset_pid,
    n_parallel_uploads=2,  # Whatever your instance can handle
)

print('Dataset created and files uploaded successfully!')

# # tabular_file = 'data/dataverses/open-source-at-harvard/datasets/open-source-at-harvard/files/2019-02-25.tsv'
# # resp = api.upload_file(dataset_pid, tabular_file)
# # print(resp)
