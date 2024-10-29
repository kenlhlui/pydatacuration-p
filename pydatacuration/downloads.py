import sys
import httpx
import orjson

class Downloads:
    def __init__(self, base_url, api_token, pid, download_dir):
        self.base_url = base_url
        self.api_token = api_token
        self.pid = pid
        self.download_dir = download_dir
        self.client = httpx.Client(headers={'X-Dataverse-key': self.api_token}, timeout=None)

    def get_ds_metadata(self):
        """Get metadata of a dataset
        
        Returns:
            dict: Metadata of the dataset
        """
        url = f"{self.base_url}/api/datasets/:persistentId/?persistentId={self.pid}"
        try:
            response = self.client.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors

            with open(f'{self.download_dir}/dataset/metadata/ds_metadata.json', 'w', encoding='utf-8') as f:
                f.write(orjson.dumps(response.json(), option=orjson.OPT_INDENT_2).decode())

            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"An error occurred: {e}")
            sys.exit(1)

    def get_ds_zip(self):
        # TODO: Change to 'Download By Dataset By Version' API, if possible (it's not working now)
        """Get a dataset as a zip file

        Returns:
            str: Path to the downloaded zip file
        """
        file_path = f'{self.download_dir}/temp_data/ds.zip'
        url = self.base_url + 'api/access/dataset/:persistentId/?persistentId=' + self.pid

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
