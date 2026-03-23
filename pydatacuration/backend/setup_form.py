from pathlib import Path

from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import HttpUrl
from pydantic import field_serializer


class SetupForm(BaseModel):
    """Setup form payload."""

    main_dir: str = 'workdir'
    res_dir: str = 'res'

    @field_serializer('base_url')
    def serialize_base_url(self, v: HttpUrl | None) -> str | None:
        """Serialize HttpUrl to string.

        Args:
            v (HttpUrl | None): URL value.


        Returns:
            str | None: String URL.

        """
        return str(v) if v else None

    @field_serializer('main_dir')
    def serialize_main_dir(self, v: str) -> str:
        """Resolve and serialize path to string.

        Args:
            v (str): Path string.


        Returns:
            str: Resolved path string.

        """
        return str(Path(v).resolve())

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
