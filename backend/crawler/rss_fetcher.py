"""AWS What's New RSS フィードからエントリを取得するモジュール"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone

import feedparser

logger = logging.getLogger(__name__)

RSS_URL = "https://aws.amazon.com/about-aws/whats-new/recent/feed/"


@dataclass
class RssEntry:
    title: str
    source_url: str
    summary_en: str
    published_date: date
    category: str


def fetch_entries(since_date: date) -> list[RssEntry]:
    """RSS フィードを取得し、since_date 以降のエントリを返す"""
    logger.info("Fetching RSS feed: %s", RSS_URL)
    feed = feedparser.parse(RSS_URL)

    if feed.bozo:
        logger.warning("RSS parse warning: %s", feed.bozo_exception)

    entries: list[RssEntry] = []
    for item in feed.entries:
        published = _parse_date(item)
        if published is None or published < since_date:
            continue

        category = _extract_category(item)
        entries.append(
            RssEntry(
                title=item.get("title", "").strip(),
                source_url=item.get("link", "").strip(),
                summary_en=_clean_html(item.get("summary", "")),
                published_date=published,
                category=category,
            )
        )

    logger.info("Found %d entries since %s", len(entries), since_date)
    return entries


def _parse_date(item: feedparser.FeedParserDict) -> date | None:
    """feedparser エントリから公開日を取得する"""
    if hasattr(item, "published_parsed") and item.published_parsed:
        dt = datetime(*item.published_parsed[:6], tzinfo=timezone.utc)
        return dt.date()
    if hasattr(item, "updated_parsed") and item.updated_parsed:
        dt = datetime(*item.updated_parsed[:6], tzinfo=timezone.utc)
        return dt.date()
    return None


def _extract_category(item: feedparser.FeedParserDict) -> str:
    """タグからカテゴリ文字列を抽出する"""
    tags = getattr(item, "tags", [])
    if not tags:
        return ""
    # "general:products/amazon-s3" → "Amazon S3" 形式のタグから製品名を取る
    labels = [t.get("term", "") for t in tags if t.get("term")]
    return ", ".join(labels[:3])  # 最大3タグ


def _clean_html(text: str) -> str:
    """簡易HTMLタグ除去"""
    import re
    return re.sub(r"<[^>]+>", "", text).strip()
