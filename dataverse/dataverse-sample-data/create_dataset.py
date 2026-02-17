import json

import dvconfig
from pyDataverse.api import Api


base_url = dvconfig.base_url
api_token = dvconfig.api_token
api = Api(base_url, api_token)
print(api.status)
dataset_json = 'data/dataverses/toronto/dataset/toronto.json'
with open(dataset_json) as f:
    metadata = json.load(f)
dataverse = 'toronto'
resp = api.create_dataset(dataverse, json.dumps(metadata))
# print(resp)
# dataset_pid = resp.json()['data']['persistentId']
# # tabular_file = 'data/dataverses/open-source-at-harvard/datasets/open-source-at-harvard/files/2019-02-25.tsv'
# # resp = api.upload_file(dataset_pid, tabular_file)
# # print(resp)
