"""Utility functions for checklist operations."""

from pathlib import Path

import yaml
from loguru import logger
from pydantic import ValidationError

from pydatacuration.checklist.checklist_model import ChecklistYAML


def validate_checklist_yaml(yaml_path: str | Path) -> ChecklistYAML:
    """Load and validate a checklist YAML file."""
    try:
        with Path(yaml_path).open(encoding='utf-8') as f:
            data = yaml.safe_load(f)

        logger.debug(f'Validating checklist YAML file: {yaml_path}')
        return ChecklistYAML(**data)
    except (yaml.YAMLError, ValidationError) as e:
        logger.error(f'Error validating checklist YAML file: {yaml_path} - {e}')
        raise


def _get_checklist_file_path(checklist_identifier: str, res_dir: Path) -> Path:
    """Get the file path for a checklist identifier.

    Args:
        checklist_identifier (str): The checklist identifier (e.g., 'high', 'medium', 'custom').
        res_dir (Path): Path to the res directory containing checklist files.

    Returns:
        Path: Path to the checklist file.

    Raises:
        FileNotFoundError: If the resource directory or checklist file is not found.
    """
    if not res_dir.exists():
        msg = f'Resource directory not found: {res_dir}'
        raise FileNotFoundError(msg)

    for extension in ['.yaml', '.yml']:
        # Pattern 1: checklist-{identifier}.yaml
        new_pattern_file = res_dir / f'checklist-{checklist_identifier}{extension}'
        if new_pattern_file.exists():
            return new_pattern_file

        # Pattern 2: checklist.yaml (for 'default' identifier)
        if checklist_identifier == 'default':
            default_file = res_dir / f'checklist{extension}'
            if default_file.exists():
                return default_file

    msg = f'Checklist file not found for identifier: {checklist_identifier}'
    raise FileNotFoundError(msg)


def get_checklist_content(checklist_identifier: str, res_dir: Path) -> ChecklistYAML:
    """Resolve, load, and validate a checklist YAML file by identifier.

    Args:
        checklist_identifier (str): The checklist identifier (e.g., 'default', 'high').
        res_dir (Path): Path to the res directory containing checklist files.

    Returns:
        ChecklistYAML: The validated checklist content.

    Raises:
        FileNotFoundError: If the resource directory or checklist file is not found.
    """
    checklist_file = _get_checklist_file_path(checklist_identifier, res_dir)
    logger.debug(f'Using checklist file: {checklist_file}')
    return validate_checklist_yaml(checklist_file)
