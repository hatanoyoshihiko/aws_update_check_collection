"""Aurora DSQL read client for API Lambda"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

import psycopg
from db_connection import get_connection as _base_get_connection


@contextmanager
def get_connection() -> Generator[psycopg.Connection, None, None]:
    with _base_get_connection(autocommit=True) as conn:
        yield conn


def row_to_dict(description: list, row: tuple) -> dict:
    result = {}
    for col, val in zip(description, row):
        name = col.name
        result[name] = val.isoformat() if hasattr(val, "isoformat") else val
    return result
