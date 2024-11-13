# pylint: disable=C0301
import sys
import os
import httpx
import orjson
import asyncio

class Downloads:
    """Class to download a dataset from a Dataverse repository

    Args:
        base_url (str): Base URL of the Dataverse repository
        api_token (str): API token of the Dataverse repository
        pid (str): Persistent identifier of the dataset
        download_dir (str): The master directory to save the downloaded files
    """
    def __init__(self, base_url, api_token, pid, download_dir):
        self.base_url = base_url
        self.api_token = api_token
        self.pid = pid
        self.download_dir = download_dir
        self.client = httpx.Client(headers={'X-Dataverse-key': self.api_token}, timeout=None, follow_redirects=True)
        self.async_client = httpx.AsyncClient(headers={'X-Dataverse-key': self.api_token}, timeout=None, follow_redirects=True)

    def _metadata_dir(self):
        """Create the metadata directory
        """
        if not os.path.exists(f'{self.download_dir}/dataset/metadata'):
            os.makedirs(f'{self.download_dir}/dataset/metadata', exist_ok=True)
        metadata_dir = f'{self.download_dir}/dataset/metadata'

        return metadata_dir

    def _files_dir(self):
        """Create the files directory
        """
        if not os.path.exists(f'{self.download_dir}/temp_data'):
            os.makedirs(f'{self.download_dir}/temp_data', exist_ok=True)

        files_dir = f'{self.download_dir}/temp_data'

        return files_dir

    def _get_data_file(self, file_id, file_path):
        """Get the data file of the dataset
        
        Returns:
            str: Path to the downloaded data file
        """
        url = f'{self.base_url}/api/access/datafile/{file_id}'
        file_path = f'{self.download_dir}/temp_data/{file_path}'
        try:
            with self.client.stream("GET", url, params={'format': 'original'}) as response:
                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_bytes():
                            f.write(chunk)
                return file_path
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            sys.exit(1)

    async def _get_data_file_async(self, file_id, file_path):
        """Get the data file of the dataset asynchronously
        
        Returns:
            str: Path to the downloaded data file
        """
        url = f'{self.base_url}/api/access/datafile/{file_id}'
        file_path = f'{self.download_dir}/temp_data/{file_path}'
        try:
            async with self.async_client.stream("GET", url, params={'format': 'original'}) as response:
                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        async for chunk in response.aiter_bytes():
                            f.write(chunk)
                return file_path
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            sys.exit(1)

    def _get_ds_metadata(self):
        """Get metadata of a dataset
        
        Returns:
            dict: Metadata of the dataset
        """
        url = f"{self.base_url}/api/datasets/:persistentId/?persistentId={self.pid}"

        try:
            response = self.client.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"An error occurred: {e}")
            sys.exit(1)

    def save_ds_metadata(self):
        """Save the dataset metadata to a JSON file
        """
        file_path = os.path.join(self._metadata_dir(), 'ds_metadata.json')
        try:
            response = self._get_ds_metadata()
            if response.status_code == 200:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(orjson.dumps(response.json(), option=orjson.OPT_INDENT_2).decode())
        except Exception as e:
            print(f" An error occurred: {e}")
            sys.exit(1)

    def get_ds_zip(self):
        # TODO: Change to 'Download By Dataset By Version' API, if possible (it's not working now)
        """Get a dataset as a zip file

        Returns:
            str: Path to the downloaded zip file
        """
        file_path = os.path.join(self._files_dir(), 'ds.zip')
        url = self.base_url + 'api/access/dataset/:persistentId/?persistentId=' + self.pid + '&format=original'

        try:
            with self.client.stream("GET", url) as response:
                response.raise_for_status()
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_bytes():
                        f.write(chunk)
            return file_path

        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            sys.exit(1)

        except Exception as e:
            print(f"An error occurred: {e}")
            sys.exit(1)

    async def async_get_ds_zip(self):
        """Get a dataset as a zip file asynchronously

        Returns:
            str: Path to the downloaded zip file
        """
        file_path = os.path.join(self._files_dir(), 'ds.zip')
        url = self.base_url + 'api/access/dataset/:persistentId/?persistentId=' + self.pid + '&format=original'

        try:
            async with self.async_client.stream("GET", url) as response:
                response.raise_for_status()
                with open(file_path, 'wb') as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)
            return file_path

        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            sys.exit(1)

        except Exception as e:
            print(f"An error occurred: {e}")
            sys.exit(1)
