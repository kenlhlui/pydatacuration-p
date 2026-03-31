"""Status options for checklist items in the frontend."""

from pathlib import Path

import orjson
import yaml
from pydantic import BaseModel
from pydantic import Field


class StatusOptions(BaseModel):
    """Model for the main directory."""

    Pass: str = Field(
        'Pass', serialization_alias='Pass', description='Checklist item is complete and meets all requirements.'
    )
    Follow_up: str = Field(
        'Follow-up', serialization_alias='Follow-up', description='Checklist item requires follow-up action.'
    )
    TBD: str = Field(
        'To Be Determined',
        serialization_alias='To Be Determined',
        description='Checklist item status is pending determination.',
    )
    NA: str = Field(
        'Not Applicable', serialization_alias='Not Applicable', description='Checklist item is not applicable.'
    )


def load_status_options(res_dir: str | Path) -> StatusOptions:
    """Load StatusOptions from a YAML or JSON file in res_dir.

        - If file exists: file is the complete source of truth.
        - If file is missing: returns pure defaults.

    Args:
        res_dir (str | Path): Path to the resources directory containing the status options file.

    Returns:
        StatusOptions: The loaded status options.
    """
    res_dir = Path(res_dir)

    # Safely get the first match, or None if no file found
    file_path = next(res_dir.glob('status_options.*'), None)

    if file_path is None:
        return StatusOptions()  # pure defaults

    raw = file_path.read_text(encoding='utf-8')
    data = yaml.safe_load(raw) if file_path.suffix in {'.yaml', '.yml'} else orjson.loads(raw)

    return StatusOptions.model_validate(data)
