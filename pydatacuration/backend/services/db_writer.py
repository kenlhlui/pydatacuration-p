"""Database writer functions for writing metadata to the database."""

from loguru import logger

from pydatacuration.checker.checker import Checker
from pydatacuration.checklist.checklist_model import ChecklistYAML
from pydatacuration.db import DatabaseBackend
from pydatacuration.utils.utils import parse_dataset_url


# The below writes the to the database database
def write_project_metadata_to_db(db_instance: DatabaseBackend, checker: Checker) -> None:
    """Write the project metadata to the database.

    Args:
        db_instance (DatabaseBackend): The database instance to write to.
        checker (Checker): The Checker instance containing the dataset metadata.

    """
    try:
        # Get the project metadata schema from the database instance
        project_metadata_schema = db_instance.models.project_metadata_record()

        # Extract the necessary metadata from the checker instance
        project_number = db_instance.schema_name
        curator_name: str | None = checker.curator_name
        curator_email: str | None = checker.curator_email
        dataset_title = checker.ds_title if checker.ds_title else 'No Title'
        dataset_pid = checker.ds_metadata.get('data', {}).get('latestVersion', {}).get('datasetPersistentId', 'No ID')
        datasetid = checker.ds_metadata.get('data', {}).get('latestVersion', {}).get('datasetId', 'No ID')
        dataset_url = parse_dataset_url(checker.base_url, dataset_pid)
        dataset_path = checker.get_ds_path()

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
        raise


def write_checklist_metadata_to_db(db_instance: DatabaseBackend, checklist: ChecklistYAML) -> None:
    """Write the checklist metadata to database.

    Args:
        db_instance (DatabaseBackend): The database instance to write to.
        checklist (ChecklistYAML): The checklist content to write.
    """
    try:
        checklist_metadata_schema = db_instance.models.checklist_metadata()

        metadata = checklist.checklist_metadata
        db_instance.merge_records_to_table(
            checklist_metadata_schema(
                name=metadata.name,
                version=metadata.version,
                description=metadata.description,
                created_by=metadata.created_by,
                last_updated=metadata.last_updated,
                status=metadata.status,
            )
        )
    except Exception as e:
        logger.error(f'Failed to write checklist metadata to database: {e}')
        raise


def write_checklist_items_to_db(db_instance: DatabaseBackend, checklist: ChecklistYAML) -> None:
    """Write the checklist items to database.

    Args:
        db_instance (DatabaseBackend): The database instance to write to.
        checklist (ChecklistYAML): The checklist content to write.
    """
    try:
        checklist_schema = db_instance.models.checklist()

        for item in checklist.checklist:
            logger.debug(f'Writing checklist item to database: {item.id}')
            db_instance.merge_records_to_table(
                checklist_schema(
                    id=item.id,
                    action=item.action,
                    instructions=item.instructions,
                    priority=item.priority,
                    section=item.section,
                    automated_check_ids=item.automated_check_ids,
                    tool_explanation=item.tool_explanation,
                    curator_check_item=item.curator_check_item,
                    check_type=item.check_type,
                )
            )
    except Exception as e:
        logger.error(f'Failed to write checklist to database: {e}')
        raise
