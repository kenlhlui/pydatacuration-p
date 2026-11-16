"""Custom exceptions for the package, and how errors are shown to users."""

import traceback
from typing import ClassVar
from uuid import uuid4

from loguru import logger

from pydatacuration.i18n import t


class UserFacingError(Exception):
    """An error with a message for users, taken from the catalogue by message_key.

    str(exc) is the detail for the log; it is never shown to users.
    """

    message_key: ClassVar[str] = 'errors.unexpected'

    def __init__(self, detail: str = '', **params: object) -> None:
        """Initialize the error.

        Args:
            detail (str): Detail for the log.
            **params: Values for the placeholders in the user message.
        """
        super().__init__(detail)
        self.params = params


class DatasetAccessError(UserFacingError):
    """Raised when there are issues accessing a dataset."""

    message_key = 'errors.dataset_access'


class DatasetUnauthorizedError(DatasetAccessError):
    """Raised when the user does not have access to the dataset."""

    message_key = 'errors.dataset_unauthorized'


class DatasetNotFoundError(DatasetAccessError):
    """Raised when the dataset does not exist."""

    message_key = 'errors.dataset_not_found'


class SchemaVersionError(Exception):
    """Raised when the database's schema version does not match the version the code expects."""


class DirectoryExistsError(UserFacingError):
    """Raised when the working directory already exists and force_delete is not set. Pass project_number."""

    message_key = 'errors.project_exists'


class FileMatchError(UserFacingError):
    """Raised when the downloaded files do not match the metadata JSON file."""

    message_key = 'errors.file_mismatch'


def describe_error(exc: BaseException) -> str:
    """Log an error with a new reference ID, and return the message to show the user.

    The message is generic text from the catalogue plus the reference ID; the exception's own text and traceback
    only go to the log, under that ID. The traceback is formatted without variable values (unlike loguru's
    exception logging), so values such as API tokens don't end up in the log.

    Args:
        exc (BaseException): The error.

    Returns:
        str: The message for the user, e.g. 'Something went wrong. Reference: 3f9a1c2e'.
    """
    error_id = uuid4().hex[:8]
    # First line: the reference as the user sees it, and the error, so searching the log for either finds it
    details = ''.join(traceback.format_exception(exc)).rstrip()
    logger.error(f'Reference: {error_id} | {type(exc).__name__}: {exc}\n{details}')
    message = t(exc.message_key, **exc.params) if isinstance(exc, UserFacingError) else t('errors.unexpected')
    return f'{message} {t("errors.reference", error_id=error_id)}'
