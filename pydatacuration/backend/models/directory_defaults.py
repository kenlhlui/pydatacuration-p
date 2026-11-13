"""This module defines the DirectoryDefaults model, which contains shared directory fields for the application."""

from pathlib import Path

from pydantic import BaseModel
from pydantic import DirectoryPath
from pydantic import Field


class MainDir(BaseModel):
    """Model for the main directory."""

    main_dir: DirectoryPath = Field(Path('workdir'), description='Main working directory. Must already exist.')


class ResDir(BaseModel):
    """Model for the resources directory."""

    res_dir: DirectoryPath = Field(Path('res'), description='Resources directory. Must already exist.')


class DirectoryDefaults(MainDir, ResDir):
    """Shared directory fields."""
