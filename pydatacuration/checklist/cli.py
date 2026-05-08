"""CLI for validating checklist YAML files."""

import argparse
from sys import exit

from loguru import logger
from pydantic import ValidationError

from .utils import validate_checklist_yaml


def main() -> None:
    """Main function for the checklist YAML validation CLI."""
    parser = argparse.ArgumentParser()
    parser.add_argument('yaml_path')
    args = parser.parse_args()

    try:
        validate_checklist_yaml(args.yaml_path)
        logger.success('✅ Valid')

    except ValidationError:
        logger.error('❌ Invalid')
        exit(1)

    except Exception as e:
        logger.error('❌ Invalid')
        logger.error(e)
        exit(1)


if __name__ == '__main__':
    main()
