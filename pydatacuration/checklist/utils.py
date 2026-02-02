"""Utility functions for checklist operations."""

from pathlib import Path

import yaml
from loguru import logger

from pydatacuration.checklist.checklist_model import ChecklistYAML


def validate_checklist_yaml(yaml_path: str | Path) -> ChecklistYAML:
    """Load and validate a checklist YAML file."""
    with Path(yaml_path).open(encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # This will raise ValidationError if the YAML doesn't match the schema
    logger.debug(f'Validating checklist YAML file: {yaml_path}')
    return ChecklistYAML(**data)


def get_checklist_file_path(checklist_identifier: str, res_dir: Path) -> Path | None:
    """Get the file path for a checklist identifier.

    Args:
        checklist_identifier (str): The checklist identifier (e.g., 'high', 'medium', 'custom').
        res_dir (Path): Path to the res directory containing checklist files.

    Returns:
        Path | None: Path to the checklist file if found, None otherwise.
    """
    if not res_dir.exists():
        logger.warning(f'Resource directory not found: {res_dir}')
        return None

    # Check for new naming patterns first
    for extension in ['.yaml', '.yml']:
        # Pattern 1: checklist-{identifier}.yaml
        new_pattern_file = res_dir / f'checklist-{checklist_identifier}{extension}'
        if new_pattern_file.exists():
            validate_checklist_yaml(new_pattern_file)
            return new_pattern_file

        # Pattern 2: checklist.yaml (for 'default' identifier)
        if checklist_identifier == 'default':
            default_file = res_dir / f'checklist{extension}'
            if default_file.exists():
                validate_checklist_yaml(default_file)
                return default_file

    # Pattern 3: Backward compatibility with check-list_template_{identifier}.yaml
    legacy_file = res_dir / f'check-list_template_{checklist_identifier}.yaml'
    if legacy_file.exists():
        validate_checklist_yaml(legacy_file)
        return legacy_file

    logger.warning(f'Checklist file not found for identifier: {checklist_identifier}')
    return None
