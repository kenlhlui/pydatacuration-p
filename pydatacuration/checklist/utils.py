"""Utility functions for checklist operations."""

from pathlib import Path

import yaml
from loguru import logger
from pydantic import ValidationError

from pydatacuration.checklist.checklist_model import ChecklistYAML


def validate_checklist_yaml_content(yaml_content: str) -> ChecklistYAML:
    """Validate checklist YAML content from a string."""
    try:
        data = yaml.safe_load(yaml_content)
        return ChecklistYAML(**data)
    except (yaml.YAMLError, ValidationError) as e:
        logger.error(f'Error validating checklist YAML content: {e}')
        raise


def validate_checklist_yaml(yaml_path: str | Path) -> ChecklistYAML:
    """Load and validate a checklist YAML file."""
    try:
        with Path(yaml_path).open(encoding='utf-8') as f:
            logger.debug(f'Validating checklist YAML file: {yaml_path}')
            return validate_checklist_yaml_content(f.read())
    except (yaml.YAMLError, ValidationError) as e:
        logger.error(f'Error validating checklist YAML file: {yaml_path} - {e}')
        raise


def get_checklist_paths_from_res_dir(res_dir: Path) -> list[Path]:
    """Get checklist file paths from the resource directory."""
    checklist_paths = []
    checklist_paths.extend(res_dir.glob('checklist-*.yaml'))
    checklist_paths.extend(res_dir.glob('checklist-*.yml'))
    return checklist_paths


def get_validated_checklist_paths(checklist_paths: list[Path]) -> dict[str, Path]:
    """Discover and validate checklist YAML files in the resource directory.

    Args:
        checklist_paths (list[Path]): List of paths to checklist YAML files.

    Returns:
        dict[str, Path]: Dictionary mapping checklist identifiers to their file paths.
    """
    validated_checklists = []
    try:
        for path in checklist_paths:
            validated_checklists.append(validate_checklist_yaml(path))
    except Exception as e:
        logger.error(f'Error occurred while validating checklist file: {path} - {e}')

    return {f'{f.name}': f for f in validated_checklists}


def get_checklist_names_from_paths(checklist_paths: dict[str, Path]) -> dict[str, str]:
    """Extract checklist identifiers and display names from file paths.

    Args:
        checklist_paths (dict[str, Path]): Dictionary mapping checklist identifiers to their file paths.

    Returns:
        dict[str, str]: Dictionary mapping checklist identifiers to display names.
    """
    checklist_options = {}
    for identifier, path in checklist_paths.items():
        # Read the yaml file and get the alias or name field for display
        try:
            checklist_yaml = validate_checklist_yaml(path)
            display_name = checklist_yaml.checklist_metadata.alias or checklist_yaml.checklist_metadata.name
            checklist_options[identifier] = display_name
        except Exception as e:
            logger.error(f'Error occurred while processing checklist file: {path} - {e}')

    return checklist_options


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
    validated_checklist_paths = get_validated_checklist_paths(checklist_paths)
    checklist_options = get_checklist_names_from_paths(validated_checklist_paths)

    return checklist_options
