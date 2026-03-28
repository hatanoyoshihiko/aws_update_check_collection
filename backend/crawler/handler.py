"""Crawler Lambda エントリポイント

EventBridge Scheduler から呼び出される。
環境変数:
  DSQL_ENDPOINT   - Aurora DSQL エンドポイント
  DSQL_REGION     - Aurora DSQL リージョン (default: us-east-1)
  DSQL_DATABASE   - データベース名 (default: postgres)
  BEDROCK_MODEL_ID - Bedrock モデルID (default: jp.anthropic.claude-sonnet-4-6)
  BEDROCK_REGION  - Bedrock リージョン (default: ap-northeast-1)
  BACKFILL_DAYS   - 初回バックフィル日数 (default: 1, 初回は 30 を推奨)
"""
from __future__ import annotations

import logging
import os
from datetime import date, timedelta

from bedrock_client import generate_summary
from db_client import UpdateRecord, get_empty_records, get_existing_urls, update_bedrock_fields, upsert_update
from page_scraper import fetch_article_text
from rss_fetcher import fetch_entries

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKFILL_DAYS = int(os.environ.get("BACKFILL_DAYS", "1"))


def _run_migration() -> dict:
    """スキーママイグレーションを実行する（title_ja カラム追加）"""
    from db_client import get_connection
    sql = "ALTER TABLE aws_updates ADD COLUMN IF NOT EXISTS title_ja VARCHAR(500)"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    logger.info("Migration done")
    return {"statusCode": 200, "migration": "done"}


def _reprocess_empty() -> dict:
    """page_summary_ja / use_cases_ja が空のレコードを Bedrock で再処理する"""
    records = get_empty_records()
    logger.info("Reprocessing %d empty records", len(records))
    updated = 0
    failed = 0
    for rec in records:
        try:
            article_text = fetch_article_text(rec["source_url"])
            result = generate_summary(rec["title"], article_text or rec.get("summary_en", ""))
            update_bedrock_fields(rec["id"], result.title_ja, result.page_summary_ja, result.use_cases_ja)
            updated += 1
            logger.info("Updated: %s", rec["title"][:60])
        except Exception as e:
            failed += 1
            logger.error("Failed to reprocess %s: %s", rec["source_url"], e)
    logger.info("Reprocess done. updated=%d, failed=%d", updated, failed)
    return {"statusCode": 200, "updated": updated, "failed": failed}


def lambda_handler(event: dict, context: object) -> dict:
    if event.get("run_migration"):
        return _run_migration()
    if event.get("reprocess_empty"):
        return _reprocess_empty()

    since_date = date.today() - timedelta(days=BACKFILL_DAYS)
    logger.info("Collecting updates since %s", since_date)

    entries = fetch_entries(since_date)
    if not entries:
        logger.info("No new entries found")
        return {"statusCode": 200, "inserted": 0, "skipped": 0}

    # 既存URLを一括チェックして無駄なスクレイピングを省く
    all_urls = [e.source_url for e in entries]
    existing_urls = get_existing_urls(all_urls)
    new_entries = [e for e in entries if e.source_url not in existing_urls]
    logger.info(
        "New entries: %d / Total: %d (skipping %d duplicates)",
        len(new_entries),
        len(entries),
        len(existing_urls),
    )

    inserted = 0
    skipped = 0
    for entry in new_entries:
        article_text = fetch_article_text(entry.source_url)
        bedrock_result = generate_summary(entry.title, article_text or entry.summary_en)

        record = UpdateRecord(
            published_date=entry.published_date,
            title=entry.title,
            title_ja=bedrock_result.title_ja,
            summary_en=entry.summary_en,
            source_url=entry.source_url,
            page_summary_ja=bedrock_result.page_summary_ja,
            use_cases_ja=bedrock_result.use_cases_ja,
            category=entry.category,
        )
        if upsert_update(record):
            inserted += 1
            logger.info("Inserted: %s", entry.title[:60])
        else:
            skipped += 1

    logger.info("Done. inserted=%d, skipped=%d", inserted, skipped)
    return {"statusCode": 200, "inserted": inserted, "skipped": skipped}


if __name__ == "__main__":
    # ローカル動作確認用
    result = lambda_handler({}, None)
    print(result)
