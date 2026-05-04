from pydatacuration.services.api_calls.httpx_client import HTTPXClient


class DVAPICalls:
    """Class to call the Dataverse API."""

    def __init__(self, httpx_client: HTTPXClient) -> None:
        """Initialize the DVAPICalls class."""
        self.httpx_client = httpx_client

    def get_depositor_record(self, depositor: str, collection_alias: str | None = None) -> dict:
        """Get the depositor record from the Dataverse repository using the search API.

            - Check if the depositor has record by search API
            - See https://github.com/IQSS/dataverse/issues/2038 for fq field;
            - Note that fq supports searching the fields of the database schema
            - i.e. The fields in the Native JSON export of a dataset
            - The schema can be found inside the .tsv files for each metadata block: https://github.com/IQSS/dataverse/tree/master/scripts/api/data/metadatablocks

        Returns:
            dict: A dictionary containing the dataverse tree information.
        """
        # If collection_alias is provided, search within the specified dataverse collection
        if collection_alias:
            response = self.httpx_client.sync_get(
                f'/api/search?q=*&type=dataset&per_page=1000&subtree={collection_alias}&fq=depositor:"{depositor}"'
            )  # noqa: E501
            return response.json()
        # If no collection_alias is provided, search in all dataverses
        response = self.httpx_client.sync_get(f'/api/search?q=*&type=dataset&per_page=1000&fq=depositor:"{depositor}"')  # noqa: E501
        return response.json()
