"""Database writer functions for writing metadata to the database."""

from pathlib import Path

import yaml
from loguru import logger

from pydatacuration.checklist.utils import get_checklist_file_path
from pydatacuration.utils.utils import parse_dataset_url


RES_DIR = Path('res')  # FIXME: Should not use a hardcoded path


# The below writes the to the database database
def write_project_metadata(db_instance, checker) -> None:
    """Write the project metadata to the database."""
    project_metadata_schema = db_instance.models.project_metadata_record()

    # Check if record already exists
    try:
        project_number = db_instance.schema_name
        curator_name: str | None = checker.curator_name
        curator_email: str | None = checker.curator_email
        dataset_title = checker.ds_title if checker.ds_title else 'No Title'
        dataset_pid = checker.ds_metadata.get('data', {}).get('latestVersion', {}).get('datasetPersistentId', 'No ID')
        datasetid = checker.ds_metadata.get('data', {}).get('latestVersion', {}).get('datasetId', 'No ID')
        dataset_url = parse_dataset_url(checker.base_url, dataset_pid)
        dataset_path = checker.check_ds_tree_info()

        db_instance.merge_records_to_table(
            project_metadata_schema(
                curator_name=curator_name,
                curator_email=curator_email,
                project_number=project_number,
                dataset_title=dataset_title,
                dataset_pid=dataset_pid,
                dataset_id=checker.dataset_id,
                datasetid=datasetid,
                dataset_url=dataset_url,
                dataset_path=dataset_path,
                checklist_type=checker.checklist_type,
            )
        )
    except Exception as e:
        logger.error(f'Failed to write to database: {e}')


def write_checklist_metadata(db, body) -> None:
    pass


def write_checklist_items(db_instance, checklist_type) -> None:
    """Write the checklist items to database.

    Supports flexible checklist file naming:
    - Checklist with types: checklist-{type}.yaml or checklist-{type}.yml
    - Default: checklist.yaml or checklist.yml (when checklist_type='default')

    Args:
        checklist_type (str): Type of checklist to use. Default is 'default'
    """
    try:
        logger.debug(f'Writing the {checklist_type} checklist to database...')
        checklist_schema = db_instance.models.checklist()

        # Use the flexible file path function to find the checklist file
        checklist_file: Path | None = get_checklist_file_path(checklist_type, RES_DIR)

        if not checklist_file or not checklist_file.exists():
            error_msg = f'Checklist file not found for type: {checklist_type}'
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        logger.debug(f'Using checklist file: {checklist_file}')

        with Path.open(checklist_file, 'r') as f:
            checklist_data = yaml.safe_load(f)

        # Write each checklist item to database
        for item in checklist_data.get('checklist', []):
            logger.debug(f'Writing checklist item to database: {item}')
            db_instance.merge_records_to_table(
                checklist_schema(
                    id=item.get('id'),
                    action=item.get('action'),
                    instructions=item.get('instructions'),
                    priority=item.get('priority'),
                    section=item.get('section'),
                    automated_check_ids=item.get('automated_check_ids'),
                    tool_explanation=item.get('tool_explanation'),
                    curator_check_item=item.get('curator_check_item'),
                    check_type=item.get('check_type'),
                )
            )
    except Exception as e:
        logger.error(f'Failed to write checklist to database: {e}')
