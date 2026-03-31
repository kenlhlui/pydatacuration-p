"""Status options for checklist items in the frontend."""

from pathlib import Path

import orjson
import yaml
from loguru import logger
from pydantic import BaseModel
from pydantic import Field
from pydantic import RootModel


class StatusOptions(BaseModel):
    """Default status options with full metadata."""

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

    def color_map(self) -> dict[str, tuple[str, str]]:
        """Map each label to (background_color, text_color)."""
        return {
            self.Pass: ('#d4edda', '#155724'),
            self.Follow_up: ('#f8d7da', '#721c24'),
            self.TBD: ('#fff3cd', '#856404'),
            self.NA: ('#e2e3e5', '#383d41'),
        }


class CustomStatusOptions(RootModel[dict[str, str]]):
    """Arbitrary status options loaded from a file."""

    root: dict[str, str]

    def color_map(self) -> dict[str, tuple[str, str]]:
        """Neutral fallback color for all custom labels."""
        return dict.fromkeys(self.root.values(), ('#e2e3e5', '#383d41'))


def load_status_options(res_dir: str | Path) -> StatusOptions | CustomStatusOptions:
    """Load StatusOptions from a YAML or JSON file in res_dir.

        - If file exists: file is the complete source of truth.
        - If file is missing: returns pure defaults.

    Args:
        res_dir (str | Path): Path to the resources directory containing the status options file.

    Returns:
        StatusOptions | CustomStatusOptions: The loaded status options.
    """
    res_dir = Path(res_dir)

    # Safely get the first match, or None if no file found
    file_path = next(res_dir.glob('status_options.*'), None)

    if file_path is None:
        logger.debug(f'No status options file found in {res_dir}. Using pure defaults.')
        return StatusOptions()

    try:
        logger.debug(f'Found status options file: {file_path}')
        raw = file_path.read_text(encoding='utf-8')
        data = yaml.safe_load(raw) if file_path.suffix in {'.yaml', '.yml'} else orjson.loads(raw)
        logger.debug(f'Loaded status options from {file_path}: {data}')
        return CustomStatusOptions.model_validate(data)
    except Exception as e:
        logger.error(f'Error reading status options file {file_path}: {e}')
        logger.info('Falling back to pure defaults of status options.')
        return StatusOptions()
