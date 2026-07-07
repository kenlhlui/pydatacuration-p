"""Module to process OAI-ORE metadata files and get the dataset path."""


def _extract_path(node: dict, dataset_name: str | None) -> str:
    """Walk schema:isPartOf chain from leaf to root, return ordered path."""
    names = []
    current = node
    while current:
        names.append(current.get('schema:name'))
        current = current.get('schema:isPartOf')
    collections_path = '/'.join(reversed(names))
    return f'{collections_path}/{dataset_name}' if dataset_name else collections_path


def get_path_from_oaiore(oai_ore_metadata: dict) -> str | None:
    """Extract the dataset path from the OAI-ORE metadata, or None if not nested in a collection."""
    if not isinstance(oai_ore_metadata, dict):
        return None
    describes = oai_ore_metadata.get('ore:describes', {})
    ispartof = describes.get('schema:isPartOf')
    if not ispartof:
        return None
    return _extract_path(ispartof, describes.get('schema:name'))
