"""The setup form models."""

from pathlib import Path

from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import HttpUrl
from pydantic import field_serializer
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

from pydatacuration.backend.models.directory_defaults import MainDir
from pydatacuration.backend.models.directory_defaults import ResDir


class SetupBase(BaseModel):
    """Shared fields for setup models."""

    base_url: HttpUrl | None = None
    api_token: str | None = None

    pid: str = ''
    project_number: str = ''
    collection_alias: str | None = None

    curator_name: str = ''
    curator_email: EmailStr | None = None

    force_delete: bool = False
    check_zip: bool = True
    checklist: str = ''


class SetupForm(SetupBase, MainDir, ResDir):
    """Setup form payload."""

    @field_serializer('base_url')
    def serialize_base_url(self, v: HttpUrl | None) -> str | None:  # noqa: PLR6301
        """Serialize HttpUrl to string.

        Args:
            v (HttpUrl | None): URL value.

        Returns:
            str | None: String URL.
        """
        return str(v) if v else None

    @field_serializer('main_dir', 'res_dir')
    def serialize_dir(self, v: str) -> str:  # noqa: PLR6301
        """Resolve and serialize path to string.

        Args:
            v (str): Path string.

        Returns:
            str: Resolved path string.
        """
        return str(Path(v).resolve())


class SetupDefaults(SetupBase, BaseSettings):
    """Environment-based default values for the setup form."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )
