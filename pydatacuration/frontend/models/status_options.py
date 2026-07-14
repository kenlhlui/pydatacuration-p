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

    Pass: str = Field('Pass', alias='Pass', description='Checklist item is complete and meets all requirements.')
    Follow_up: str = Field('Follow-up', alias='Follow-up', description='Checklist item requires follow-up action.')
    TBD: str = Field(
        'To Be Determined',
        alias='To Be Determined',
        description='Checklist item status is pending determination.',
    )
    NA: str = Field('Not Applicable', alias='Not Applicable', description='Checklist item is not applicable.')

    def color_map(self) -> dict[str, tuple[str, str]]:
        """Map each label to (background_color, text_color)."""
        return {
            self.Pass: ('#556B2F', '#ffffff00'),
            self.Follow_up: ('#C8102E', '#ffffff00'),
            self.TBD: ('#E35205', '#ffffff00'),
            self.NA: ('#333333', '#ffffff00'),
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

    # Safely get the first match for supported extensions, or None if no file found
    file_path = next(
        (
            p
            for ext in ('status_options.yaml', 'status_options.yml', 'status_options.json')
            if (p := res_dir / ext).exists()
        ),
        None,
    )

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
