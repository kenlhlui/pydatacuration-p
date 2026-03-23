from pydantic import EmailStr
from pydantic import HttpUrl
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class SetupDefaults(BaseSettings):
    """Environment-based default values for the setup form."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )

    base_url: HttpUrl | None = None
    api_token: str | None = None

    pid: str = ''
    ticket_number: str = ''
    collection_alias: str | None = None

    curator_name: str = ''
    curator_email: EmailStr | None = None

    force_delete: bool = False
    check_zip: bool = True
    checklist: str = ''
