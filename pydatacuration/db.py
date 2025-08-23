# The duckdb database connection class

from pathlib import Path

import duckdb


class DuckDBConnection:
    """DuckDB database connection class."""

    _instance = None

    def __new__(cls, db_path: Path):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db_path: Path) -> None:
        if not hasattr(self, 'initialized'):
            self.db_path = db_path
            self.connection = None
            self.initialized = True

    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
