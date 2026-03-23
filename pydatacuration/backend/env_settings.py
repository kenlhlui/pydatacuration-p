"""The fastapi setting for the backend API."""

from pydantic_settings import BaseSettings


class EnvSettings(BaseSettings):
    """Application settings loaded from .env file."""

    # Database and Core
    main_dir: str = 'workdir'
    res_dir: str = 'res'

    # Dataverse API defaults
    base_url: str | None = None
    api_token: str | None = None

    # Project defaults
    pid: str = ''
    ticket_number: str = ''
    collection_alias: str | None = None

    # Curator defaults
    curator_name: str = ''
    curator_email: str = ''

    # Processing options
    force_delete: bool = False
    check_zip: bool = True
    check_list: str = 'high'

    # Application settings
    app_port: int = 9005
    app_title: str = 'PyDataCuration'
    debug: bool = False

    class Config:
        """Pydantic config."""

        env_file: str = '.env'
        env_file_encoding: str = 'utf-8'
        case_sensitive: bool = False
        extra: str = 'allow'
