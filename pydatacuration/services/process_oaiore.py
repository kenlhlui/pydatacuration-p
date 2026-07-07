"""Module to process OAI-ORE metadata files and get the dataset path."""

from loguru import logger
from pydantic import BaseModel
from pydantic import Field
from pydantic import ValidationError


class OaiOreDescribes(BaseModel):
    model_config = {'extra': 'allow'}

    schema_name: str | None = Field(alias='schema:name', default=None)
    schema_is_part_of: dict | None = Field(
        alias='schema:isPartOf',
        default=None,
    )


class OaiOre(BaseModel):
    model_config = {'extra': 'allow'}

    ore_describes: OaiOreDescribes = Field(alias='ore:describes')


def _extract_path(node: dict | None, dataset_name: str | None) -> str:
    """Walk schema:isPartOf chain from leaf to root, return ordered path."""
    names: list[str] = []
    current = node
    while current:
        name = current.get('schema:name')
        if name:
            names.append(name)
        current = current.get('schema:isPartOf')
    names.reverse()
    if dataset_name:
        names.append(dataset_name)
    return '/'.join(names)


def get_path_from_oaiore(oai_ore_metadata: dict) -> str | None:
    """Extract the dataset path from the OAI-ORE metadata, or None if not nested in a collection."""
    try:
        ore = OaiOre.model_validate(oai_ore_metadata)
    except ValidationError as e:
        logger.error(f'Error validating OAI-ORE metadata: {e}. No dataset path can be extracted.')
        return None

    describes = ore.ore_describes
    ispartof = describes.schema_is_part_of
    return _extract_path(ispartof, describes.schema_name)
