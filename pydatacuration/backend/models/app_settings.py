"""The base application settings."""

from typing import Literal
from typing import get_args

from pydantic import Field
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

    app_port: int = Field(9005, description='The port number for the NiceGUI app to listen on.')
    app_title: str = Field('Dataverse Curation Review Tool', description='The title of the NiceGUI app.')
    app_favicon: str = Field('🔬', description='The favicon for the NiceGUI app.')
    log_level: allowed_logging_levels = Field('INFO', description='The logging level for the application.')
    app_reload: bool = Field(False, description='Whether to enable auto-reload for the NiceGUI app.')
    app_reconnect_timeout: int = Field(60, description='The timeout for reconnection attempts.')

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
