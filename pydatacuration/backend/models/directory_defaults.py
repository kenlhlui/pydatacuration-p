"""This module defines the DirectoryDefaults model, which contains shared directory fields for the application."""

from pathlib import Path

from pydantic import BaseModel
from pydantic import DirectoryPath


class MainDir(BaseModel):
    """Model for the main directory."""

    main_dir: DirectoryPath = Path('workdir')


class ResDir(BaseModel):
    """Model for the resources directory."""

    res_dir: DirectoryPath = Path('res')


class DirectoryDefaults(MainDir, ResDir):
    """Shared directory fields."""
