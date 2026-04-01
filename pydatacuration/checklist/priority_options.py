"""Priority options for checklist items."""

from pathlib import Path

import orjson
import yaml
from loguru import logger
from pydantic import BaseModel
from pydantic import Field
from pydantic import RootModel


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


class CustomPriorityOptions(RootModel[dict[str, str]]):
    """Arbitrary priority options loaded from a file."""

    root: dict[str, str]


def load_priority_options(res_dir: str | Path) -> PriorityOptions | CustomPriorityOptions:
    """Load PriorityOptions from a YAML or JSON file in res_dir.

        - If file exists: file is the complete source of truth.
        - If file is missing: returns pure defaults.

    Args:
        res_dir (str | Path): Path to the resources directory containing the priority options file.

    Returns:
        PriorityOptions | CustomPriorityOptions: The loaded priority options.
    """
    res_dir = Path(res_dir)

    # Safely get the first match for supported extensions, or None if no file found
    file_path = next(
        (
            p
            for ext in ('priority_options.yaml', 'priority_options.yml', 'priority_options.json')
            if (p := res_dir / ext).exists()
        ),
        None,
    )

    if file_path is None:
        logger.debug(f'No priority options file found in {res_dir}. Using pure defaults.')
        return PriorityOptions()  # pure defaults

    try:
        logger.debug(f'Found priority options file: {file_path}')
        raw = file_path.read_text(encoding='utf-8')
        data = yaml.safe_load(raw) if file_path.suffix in {'.yaml', '.yml'} else orjson.loads(raw)
        logger.debug(f'Loaded priority options from {file_path}: {data}')
        return CustomPriorityOptions.model_validate(data)
    except Exception as e:
        logger.error(f'Error reading priority options file {file_path}: {e}')
        logger.info('Falling back to pure defaults of priority options.')
        return PriorityOptions()
