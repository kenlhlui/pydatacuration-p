"""Priority options for checklist items in the frontend."""

from pathlib import Path

import orjson
import yaml
from pydantic import BaseModel
from pydantic import Field


class PriorityOptions(BaseModel):
    """Priority option labels — pure defaults, no env/file magic."""

    info: str = Field(
        'Info',
        serialization_alias='Info',
        description='Checklist item is informational only and does not require action.',
    )
    required: str = Field(
        'Required',
        serialization_alias='Required',
        description='Checklist item is required and must be completed to meet all requirements.',
    )
    recommended: str = Field(
        'Recommended',
        serialization_alias='Recommended',
        description='Checklist item is recommended but not strictly required to meet all requirements.',
    )


def load_priority_options(res_dir: str | Path) -> PriorityOptions:
    """Load PriorityOptions from a YAML or JSON file in res_dir.

        - If file exists: file is the complete source of truth.
        - If file is missing: returns pure defaults.

    Args:
        res_dir (str | Path): Path to the resources directory containing the priority options file.

    Returns:
        PriorityOptions: The loaded priority options.
    """
    res_dir = Path(res_dir)

    # Safely get the first match, or None if no file found
    file_path = next(res_dir.glob('priority_options.*'), None)

    if file_path is None:
        return PriorityOptions()  # pure defaults

    raw = file_path.read_text(encoding='utf-8')
    data = yaml.safe_load(raw) if file_path.suffix in {'.yaml', '.yml'} else orjson.loads(raw)

    return PriorityOptions.model_validate(data)
