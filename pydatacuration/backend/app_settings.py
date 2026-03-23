from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class AppSettings(BaseSettings):
    """Application runtime settings."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )

    main_dir: str = 'workdir'
    res_dir: str = 'res'
    app_port: int = 9005
    app_title: str = 'PyDataCuration'
    app_favicon: str = '🔬'
    debug: bool = False
