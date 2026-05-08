"""Custom exceptions for the package."""


class DatasetAccessError(Exception):
    """Raised when there are issues accessing a dataset."""


class DatasetUnauthorizedError(DatasetAccessError):
    """Raised when the user does not have access to the dataset."""


class DatasetNotFoundError(DatasetAccessError):
    """Raised when the dataset does not exist."""


class DirectoryExistsError(Exception):
    """Raised when the working directory already exists and force_delete is not set."""


class FileMatchError(Exception):
    """Raised when the downloaded files do not match the metadata JSON file."""
