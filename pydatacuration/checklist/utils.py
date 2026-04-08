"""Utility functions for checklist operations."""

from pathlib import Path

import yaml
from loguru import logger
from pydatacuration.checklist.checklist_model import ChecklistYAML


def validate_checklist_yaml_content(yaml_content: str) -> ChecklistYAML:
    """Validate checklist YAML content from a string."""
    data = yaml.safe_load(yaml_content)
    return ChecklistYAML(**data)


def validate_checklist_yaml(yaml_path: str | Path) -> ChecklistYAML:
    """Load and validate a checklist YAML file."""
    with Path(yaml_path).open(encoding='utf-8') as f:
        logger.debug(f'Validating checklist YAML file: {yaml_path}')
        return validate_checklist_yaml_content(f.read())


def get_checklist_paths_from_res_dir(res_dir: Path) -> list[Path]:
    """Get checklist file paths from the resource directory."""
    checklist_paths = []
    checklist_paths.extend(res_dir.glob('checklist*.yaml'))
    checklist_paths.extend(res_dir.glob('checklist*.yml'))
    return checklist_paths


def get_validated_checklists(checklist_paths: list[Path]) -> dict[str, ChecklistYAML]:
    """Validate checklist YAML files  and return a dictionary of validated checklist models.

    Args:
        checklist_paths (list[Path]): List of paths to checklist YAML files.

    Returns:
        dict[str, ChecklistYAML]: Dictionary mapping filenames to validated checklist models.
    """
    validated_checklists: dict[str, ChecklistYAML] = {}
    for path in checklist_paths:
        try:
            validated_checklists[path.name] = validate_checklist_yaml(path)
        except Exception as e:
            logger.error(f'Error occurred while validating checklist file: {path} - {e}')

    return validated_checklists


def get_checklist_names_from_paths(checklists: dict[str, ChecklistYAML]) -> dict[str, str]:
    """Extract checklist identifiers and display names from validated checklist models.

    Args:
        checklists (dict[str, ChecklistYAML]): Dictionary mapping checklist identifiers to validated models.

    Returns:
        dict[str, str]: Dictionary mapping checklist identifiers to display names.
    """
    return {
        identifier: checklist.checklist_metadata.alias or checklist.checklist_metadata.name
        for identifier, checklist in checklists.items()
    }


def get_checklist_content(checklist_filename: str, res_dir: Path) -> ChecklistYAML:
    """Resolve, load, and validate a checklist YAML file by identifier.

    Args:
        checklist_filename (str): The filename of the checklist file.
        res_dir (Path): Path to the res directory containing checklist files.

    Returns:
        ChecklistYAML: The validated checklist content.

    """
    with Path(res_dir, checklist_filename).open(encoding='utf-8') as f:
        logger.debug(f'Loading checklist file: {checklist_filename}')
        return validate_checklist_yaml_content(f.read())


def discover_checklist_files(res_dir: Path) -> dict[str, str]:
    """Discover available checklist files in the res directory.

    Searches for checklist files matching these patterns:
    - checklist-*.yaml or checklist-*.yml
    - checklist.yaml or checklist.yml

    Args:
        res_dir (Path): Path to the res directory containing checklist files.

    Returns:
        dict[str, str]: Dictionary mapping checklist identifiers to display names.
                        Example: {'high': 'High', 'medium': 'Medium', 'custom': 'Custom'}
    """
    checklist_options = {}

    if not res_dir.exists():
        logger.warning(f'Resource directory not found: {res_dir}')
        return checklist_options

    checklist_paths: list[Path] = get_checklist_paths_from_res_dir(res_dir)
    validated_checklist_paths = get_validated_checklists(checklist_paths)
    checklist_options = get_checklist_names_from_paths(validated_checklist_paths)

    return checklist_options
