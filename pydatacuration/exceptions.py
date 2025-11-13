"""Raised when there are issues accessing a dataset."""


class DatasetAccessError(Exception):
    """Raised when there are issues accessing a dataset."""


class DatasetUnauthorizedError(DatasetAccessError):
    """Raised when the user does not have access to the dataset."""


class DatasetNotFoundError(DatasetAccessError):
    """Raised when the dataset does not exist."""
