"""The base application settings."""

from typing import Literal
from typing import get_args

from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

from pydatacuration.backend.models.directory_defaults import DirectoryDefaults


allowed_logging_levels = Literal[
    'TRACE',
    'DEBUG',
    'INFO',
    'SUCCESS',
    'WARNING',
    'ERROR',
    'CRITICAL',
]


class AppSettings(BaseSettings, DirectoryDefaults):
    """Application runtime settings."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )

    app_port: int = 9005
    app_title: str = 'Dataverse Curation Review Tool'
    app_favicon: str = '🔬'
    debug: bool = False
    log_level: allowed_logging_levels = 'INFO'

    @field_validator('log_level', mode='before')
    def validate_log_level(cls, v: str) -> str:
        """Validate that the log level is one of the allowed values.

        Args:
            v (str): The log level to validate.

        Returns:
            str: The validated log level.

        """
        v = v.upper()

        if v not in list(get_args(allowed_logging_levels)):
            msg = f'Invalid log level: {v}'
            raise ValueError(msg)
        return v
