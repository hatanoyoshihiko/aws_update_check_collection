"""API Lambda エントリポイント

エンドポイント:
  GET /updates  (page, limit, date_from, date_to, category, q)
  GET /updates/{id}
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import date

from db_client import get_connection, row_to_dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class _NotFoundError(Exception):
    pass


class _BadRequestError(Exception):
    pass


_ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "*")
_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

_CORS_HEADERS = {
    "Access-Control-Allow-Origin": _ALLOWED_ORIGIN,
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
    "Content-Type": "application/json",
}


def lambda_handler(event: dict, context: object) -> dict:
    method = event.get("httpMethod", "GET")
    path_params = event.get("pathParameters") or {}
    resource = event.get("resource", "")

    if method == "OPTIONS":
        return {"statusCode": 200, "headers": _CORS_HEADERS, "body": ""}

    try:
        if resource == "/categories":
            body = _list_categories()
        elif path_params.get("id"):
            update_id = path_params["id"]
            if not _UUID_RE.match(update_id):
                raise _BadRequestError("id must be a valid UUID")
            body = _get_update_by_id(update_id)
        else:
            qs = event.get("queryStringParameters") or {}
            body = _list_updates(qs)
    except _NotFoundError:
        return _response(404, {"error": "Not found"})
    except _BadRequestError as e:
        return _response(400, {"error": str(e)})
    except Exception as e:
        logger.exception("Unhandled error: %s", e)
        return _response(500, {"error": "Internal server error"})

    return _response(200, body)


def _list_updates(qs: dict) -> dict:
    try:
        page = min(10000, max(1, int(qs.get("page", 1))))
        limit = min(100, max(1, int(qs.get("limit", 20))))
    except (ValueError, TypeError):
        raise _BadRequestError("page and limit must be integers")
    offset = (page - 1) * limit

    conditions: list[str] = []
    params: dict = {}

    if qs.get("date_from"):
        try:
            params["date_from"] = date.fromisoformat(qs["date_from"])
        except ValueError:
            raise _BadRequestError("date_from must be YYYY-MM-DD")
        conditions.append("published_date >= %(date_from)s")

    if qs.get("date_to"):
        try:
            params["date_to"] = date.fromisoformat(qs["date_to"])
        except ValueError:
            raise _BadRequestError("date_to must be YYYY-MM-DD")
        conditions.append("published_date <= %(date_to)s")

    if qs.get("category"):
        conditions.append("category ILIKE %(category)s ESCAPE '\\'")
        params["category"] = f"%{_escape_like(qs['category'][:100])}%"

    if qs.get("q"):
        conditions.append(
            "(title ILIKE %(q)s ESCAPE '\\' OR summary_en ILIKE %(q)s ESCAPE '\\'"
            " OR page_summary_ja ILIKE %(q)s ESCAPE '\\')"
        )
        params["q"] = f"%{_escape_like(qs['q'][:200])}%"

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    count_sql = f"SELECT COUNT(*) FROM aws_updates {where}"
    list_sql = f"""
        SELECT id, published_date, title, title_ja, summary_en, source_url,
               page_summary_ja, use_cases_ja, category, collected_at
        FROM aws_updates
        {where}
        ORDER BY published_date DESC, collected_at DESC
        LIMIT %(limit)s OFFSET %(offset)s
    """
    params["limit"] = limit
    params["offset"] = offset

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(count_sql, params)
            total = cur.fetchone()[0]  # type: ignore[index]

            cur.execute(list_sql, params)
            items = [row_to_dict(cur.description, row) for row in cur.fetchall()]

    return {"items": items, "total": total, "page": page, "limit": limit}


def _list_categories() -> dict:
    sql = """
        SELECT DISTINCT category
        FROM aws_updates
        WHERE category IS NOT NULL AND category <> ''
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            raw = [row[0] for row in cur.fetchall()]
    individual: set[str] = set()
    for value in raw:
        for cat in value.split(","):
            cat = cat.strip()
            if cat:
                individual.add(cat)
    return {"categories": sorted(individual)}


def _get_update_by_id(update_id: str) -> dict:
    sql = """
        SELECT id, published_date, title, title_ja, summary_en, source_url,
               page_summary_ja, use_cases_ja, category, collected_at
        FROM aws_updates
        WHERE id = %(id)s
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, {"id": update_id})
            row = cur.fetchone()
            if row is None:
                raise _NotFoundError()
            return row_to_dict(cur.description, row)


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": _CORS_HEADERS,
        "body": json.dumps(body, ensure_ascii=False, default=str),
    }
