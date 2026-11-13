"""The setup form models."""

from collections.abc import Callable
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import Field
from pydantic import HttpUrl
from pydantic import TypeAdapter
from pydantic import ValidationError
from pydantic import field_serializer
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

from pydatacuration.backend.models.directory_defaults import MainDir
from pydatacuration.backend.models.directory_defaults import ResDir
from pydatacuration.utils.utils import validate_project_number


class SetupBase(BaseModel):
    """Shared fields for setup models."""

    base_url: HttpUrl | None = Field(
        None, description='URL of the Dataverse installation. Prefills Dataverse Base URL.'
    )
    api_token: UUID | None = Field(
        None, description='Dataverse API token. Used whenever the API Token field is left blank.'
    )

    pid: str = Field(
        '', description='Dataset persistent identifier, e.g. doi:10.80240/FK2/FCZB4A. Prefills Dataset PID.'
    )
    project_number: str = Field(
        '', description='Curation project ID, e.g. CUR-999. Letters, numbers, - and _ only. Prefills Project Number.'
    )
    collection_alias: str | None = Field(None, description='Prefills Dataverse Collection Alias.')

    curator_name: str = Field('', description='Prefills Curator Name.')
    curator_email: EmailStr | None = Field(None, description='Prefills Curator Email.')

    force_delete: bool = Field(False, description='Prefills the "Replace existing project (if exists)" option.')
    check_zip: bool = Field(True, description='Prefills the "Unzip archive files and check contents" option.')
    checklist: str = Field(
        '', description='File name of a checklist in RES_DIR, e.g. checklist-high.yaml. Prefills the checklist.'
    )

    @field_validator('project_number')
    @classmethod
    def validate_project_number(cls, value: str) -> str:
        """Validate the project number format."""
        return validate_project_number(value)


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


def validate_setup_form_input(
    model_cls: type[BaseModel], field_name: str, *, required: bool = False
) -> Callable[[Any], str | None]:
    """Shortcut for a standalone field validator."""
    field = model_cls.model_fields[field_name]
    adapter = TypeAdapter(field.annotation)

    def rule(value: Any) -> str | None:  # noqa: ANN401
        if required and not value:
            return 'This field is required'
        try:
            adapter.validate_python(value)
            return None
        except ValidationError as e:
            return e.errors()[0].get('msg', 'Invalid value') if e.errors() else 'Invalid value'

    return rule
