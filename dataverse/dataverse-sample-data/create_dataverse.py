import json

import dvconfig
from pyDataverse.api import NativeApi


base_url = dvconfig.base_url
api_token = dvconfig.api_token


# Create the API client
native_api = NativeApi(base_url, api_token)
dv_json = 'data/dataverses/toronto/toronto.json'


# Load the dataverse metadata from the JSON file
with open(dv_json) as f:
    metadata = json.load(f)


# The parent dataverse alias where the new dataverse will be. By default, it's the root dataverse.
parentdv = ':root'

# Create the dataverse
resp = native_api.create_dataverse(parent=parentdv, metadata=json.dumps(metadata))
print(resp)
