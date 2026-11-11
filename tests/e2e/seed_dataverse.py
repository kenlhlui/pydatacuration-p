# /// script
# requires-python = ">=3.12,<3.14"  # dvuploader uses nest_asyncio, which breaks httpx/anyio on 3.14
# dependencies = [
#     "dvuploader==0.3.2",
#     "httpx>=0.28,<0.29",
# ]
# ///
"""Seed a Dataverse instance with the e2e sample collection and dataset.

Run with `uv run tests/e2e/seed_dataverse.py` from the repository root. The inline dependencies keep dvuploader
(which pins old typer/tenacity versions) out of the app's lockfile.

Reads E2E_BASE_URL and E2E_API_TOKEN from the environment. Prints the new dataset's PID and, on GitHub Actions,
also writes it to $GITHUB_OUTPUT as `pid`.
"""

import json
import os
from pathlib import Path

import dvuploader as dv
import httpx


SAMPLE_DATA = Path(__file__).parent / 'sample_data'
COLLECTION_FIELDS = ('alias', 'name', 'affiliation', 'dataverseContacts', 'description', 'dataverseType')


def create_collection(client: httpx.Client) -> str:
    """Create the sample collection under the root collection and return its alias."""
    collection = json.loads((SAMPLE_DATA / 'collection.json').read_text(encoding='utf-8'))
    payload = {key: collection[key] for key in COLLECTION_FIELDS}
    client.post('/api/dataverses/:root', json=payload).raise_for_status()
    return payload['alias']


def create_dataset(client: httpx.Client, collection_alias: str) -> str:
    """Create the sample dataset as a draft (citation metadata only) and return its PID."""
    dataset = json.loads((SAMPLE_DATA / 'dataset.json').read_text(encoding='utf-8'))
    citation = dataset['datasetVersion']['metadataBlocks']['citation']
    payload = {'datasetVersion': {'metadataBlocks': {'citation': citation}}}
    response = client.post(f'/api/dataverses/{collection_alias}/datasets', json=payload)
    response.raise_for_status()
    return response.json()['data']['persistentId']


def upload_files(base_url: str, api_token: str, pid: str) -> None:
    """Upload the sample files, keeping folder labels and restricting the files in `restricted/`."""
    files = dv.add_directory(str(SAMPLE_DATA / 'files'))
    for file in files:
        file.restrict = file.directory_label == 'restricted'
    dv.DVUploader(files=files).upload(
        persistent_id=pid,
        dataverse_url=base_url,
        api_token=api_token,
        n_parallel_uploads=2,
    )


def main() -> None:
    """Create the collection and dataset, upload the files, and report the PID."""
    base_url = os.environ['E2E_BASE_URL']
    api_token = os.environ['E2E_API_TOKEN']

    with httpx.Client(base_url=base_url, headers={'X-Dataverse-key': api_token}, timeout=60) as client:
        alias = create_collection(client)
        pid = create_dataset(client, alias)

    upload_files(base_url, api_token, pid)
    print(f'Seeded dataset {pid} in collection {alias!r}')

    if github_output := os.environ.get('GITHUB_OUTPUT'):
        with Path(github_output).open('a', encoding='utf-8') as f:
            f.write(f'pid={pid}\n')


if __name__ == '__main__':
    main()
