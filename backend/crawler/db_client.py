"""Aurora DSQL write client for Crawler Lambda"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
from typing import Generator

import psycopg
from db_connection import get_connection as _base_get_connection

logger = logging.getLogger(__name__)


@contextmanager
def get_connection() -> Generator[psycopg.Connection, None, None]:
    with _base_get_connection(autocommit=False) as conn:
        yield conn


@dataclass
class UpdateRecord:
    published_date: date
    title: str
    title_ja: str
    summary_en: str
    source_url: str
    page_summary_ja: str
    use_cases_ja: str
    category: str


def upsert_update(record: UpdateRecord) -> bool:
    sql = """
        INSERT INTO aws_updates
            (published_date, title, title_ja, summary_en, source_url,
             page_summary_ja, use_cases_ja, category)
        VALUES
            (%(published_date)s, %(title)s, %(title_ja)s, %(summary_en)s, %(source_url)s,
             %(page_summary_ja)s, %(use_cases_ja)s, %(category)s)
        ON CONFLICT (source_url) DO NOTHING
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, record.__dict__)
            inserted = cur.rowcount > 0
        conn.commit()
    return inserted


def get_existing_urls(urls: list[str]) -> set[str]:
    if not urls:
        return set()
    sql = "SELECT source_url FROM aws_updates WHERE source_url = ANY(%(urls)s)"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, {"urls": urls})
            return {row[0] for row in cur.fetchall()}


def get_empty_records() -> list[dict]:
    sql = """
        SELECT id, title, summary_en, source_url
        FROM aws_updates
        WHERE (page_summary_ja IS NULL OR page_summary_ja = '')
           OR (use_cases_ja IS NULL OR use_cases_ja = '')
           OR (title_ja IS NULL OR title_ja = '')
        ORDER BY published_date DESC
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            cols = [d.name for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def update_bedrock_fields(record_id: str, title_ja: str, page_summary_ja: str, use_cases_ja: str) -> None:
    sql = """
        UPDATE aws_updates
        SET title_ja = %(title_ja)s,
            page_summary_ja = %(page_summary_ja)s,
            use_cases_ja = %(use_cases_ja)s
        WHERE id = %(id)s
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, {"id": record_id, "title_ja": title_ja, "page_summary_ja": page_summary_ja, "use_cases_ja": use_cases_ja})
        conn.commit()
