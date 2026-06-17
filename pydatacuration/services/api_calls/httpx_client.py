"""HTTPX client for handing HTTP requests and responses."""

import asyncio
from pathlib import Path
from urllib.parse import urljoin

import httpx2
from loguru import logger
from tenacity import RetryError
from tenacity import retry
from tenacity import stop_after_attempt
from tenacity import wait_fixed


class HTTPXClient:
    """HTTPX client for handling HTTP requests and responses."""

    def __init__(self, base_url: str, api_token: str) -> None:
        """Initialize the HTTPX client.

        Args:
            base_url (str): Base URL of the Dataverse repository
            api_token (str): API token of the Dataverse repository
        """
        self.base_url = base_url
        self.api_token = api_token
        self.headers = {'X-Dataverse-key': api_token}
        self.semaphore = asyncio.Semaphore(10)
        self.async_sleep_time = 0  # TODO: make this configurable

        # Create a single AsyncClient with the desired transport settings (IPv4 enforced)
        transport = httpx2.AsyncHTTPTransport(local_address='0.0.0.0')
        self._async_client = httpx2.AsyncClient(
            headers=self.headers,
            timeout=httpx2.Timeout(10.0, connect=5.0),
            follow_redirects=True,
            transport=transport,
            limits=httpx2.Limits(max_keepalive_connections=5, max_connections=10),
        )

    @property
    def async_client(self) -> httpx2.AsyncClient:
        """Return the cached AsyncClient instance."""
        return self._async_client

    async def aclose(self) -> None:
        """Close the AsyncClient when it is no longer needed."""
        await self._async_client.aclose()

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
    def sync_get(self, api_endpoint: str, raise_for_status: bool = True) -> httpx2.Response:
        """Synchronous GET request.

        Args:
            api_endpoint (str): API endpoint to be appended to the base URL.
            raise_for_status (bool): Whether to raise an exception for non-2xx status codes.

        """
        url = urljoin(self.base_url, api_endpoint)

        limits = httpx2.Limits(max_keepalive_connections=5, max_connections=10)

        with httpx2.Client(
            headers=self.headers, timeout=httpx2.Timeout(10.0, connect=5.0), follow_redirects=True, limits=limits
        ) as client:
            try:
                response = client.get(url)
                if raise_for_status:
                    response.raise_for_status()
                return response
            except httpx2.HTTPStatusError as exc:
                logger.error(f'HTTP request Error for {url}: {exc}')
                logger.error('Retrying... (max 3 attempts with 5 second delay)')
                raise exc

            except (httpx2.ConnectError, httpx2.ConnectTimeout) as exc:
                logger.error(f'HTTP Connection error occurred {url}: {exc}')
                logger.error('Retrying... (max 3 attempts with 5 second delay)')
                raise exc
            except RetryError as exc:
                logger.error(f'The retry limit has been reached for {url}: {exc}')
                raise exc

    @staticmethod
    async def write_stream_file(file_path: Path, content: bytes) -> None:
        """Write content bytes to a file."""
        # Ensure the parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        Path(file_path).touch(exist_ok=True)
        with file_path.open('wb') as f:
            f.write(content)

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
    async def async_stream_files(self, url: str, client: httpx2.AsyncClient, **kwargs) -> bytes | None:
        """Asynchronous streaming GET request that returns the full content.

        Args:
            url (str): URL to send the GET request to.
            client (httpx2.AsyncClient): The HTTPX AsyncClient instance to use.
            **kwargs: Additional keyword arguments for the request.
        """
        try:
            async with self.semaphore, client.stream('GET', url, **kwargs) as response:
                if response.is_success:
                    # Check for empty files
                    content_length = int(response.headers.get('content-length', '-1'))
                    if content_length == 0:
                        # Return empty bytes for empty files
                        return b''

                    # For non-empty files, read all content
                    content = []
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        content.append(chunk)
                    return b''.join(content)
                return None

        except httpx2.HTTPStatusError as exc:
            logger.error(f'HTTP request Error for {url}: {exc}')
            logger.error('Retrying... (max 3 attempts with 5 second delay)')
            raise
        except (httpx2.ConnectError, httpx2.ConnectTimeout) as exc:
            logger.error(f'HTTP Connection error occurred {url}: {exc}')
            logger.error('Retrying... (max 3 attempts with 5 second delay)')
            raise
        except RetryError as exc:
            logger.error(f'The retry limit has been reached for {url}: {exc}')
            raise
