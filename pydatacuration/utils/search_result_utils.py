"""Functions to work with the search results from the Dataverse API."""

from pydantic import BaseModel
from pydantic import Field


class DatasetItemModel(BaseModel):
    """A Dataverse search result item.

    Args:
        name (str | None): Dataset name.
        url (str | None): Dataset URL.
        name_of_dataverse (str | None): Dataverse name.

    Note: this is not a complete model of the search result item, but only the fields that we are interested in for now. See the documentation here https://guides.dataverse.org/en/latest/api/search.html

    """  # noqa: E501

    name: str | None = None
    url: str | None = None
    name_of_dataverse: str | None = None
    identifier_of_dataverse: str | None = None
    citation: str | None = None
    publicationStatuses: list[str] | None = None
    storageIdentifier: str | None = None
    subjects: list[str] | None = None
    fileCount: int | None = None
    versionId: int | None = None
    versionState: str | None = None
    majorVersion: int | None = None
    minorVersion: int | None = None
    createdAt: str | None = None
    updatedAt: str | None = None


class DataSetDataModel(BaseModel):
    """Dataverse search data.

    Args:
        items (list[DatasetItemModel]): Search result items.

    """

    items: list[DatasetItemModel] = Field(default_factory=list)


class DatasetSearchResultModel(BaseModel):
    """Dataverse search response.

    Args:
        data (DataSetDataModel): Search response data.

    """

    data: DataSetDataModel = Field(default_factory=DataSetDataModel)


def get_search_result(search_result: dict) -> list[dict[str, str | None]]:
    """Get dataset search results.

    Args:
        search_result (dict): The search result dictionary.


    Returns:
        list[dict[str, str | None]]: A list of dataset search results.

    """
    parsed_result = DatasetSearchResultModel.model_validate(search_result)

    return [item.model_dump() for item in parsed_result.data.items]
