"""AWS アップデート記事ページの本文を取得するモジュール"""
from __future__ import annotations

import logging
import re

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; AWSUpdateCollector/1.0; "
        "+https://github.com/hatano/aws_update_check_collection)"
    )
}
_TIMEOUT = 15  # seconds
_ALLOWED_DOMAIN = re.compile(
    r"^https://([\w-]+\.)*aws\.amazon\.com/"
    r"|^https://([\w-]+\.)*amazonaws\.com/"
)


def fetch_article_text(url: str) -> str:
    """指定URLの記事本文テキストを取得する。失敗時は空文字を返す"""
    if not _ALLOWED_DOMAIN.match(url):
        logger.warning("Skipping non-allowed URL: %s", url)
        return ""
    try:
        with requests.get(url, headers=_HEADERS, timeout=_TIMEOUT, allow_redirects=False) as resp:
            resp.raise_for_status()
            html = resp.text
    except requests.RequestException as e:
        logger.warning("Failed to fetch %s: %s", url, e)
        return ""

    soup = BeautifulSoup(html, "html.parser")

    # AWS What's New の記事本文は #aws-page-content または main タグ内
    content_el = (
        soup.find(id="aws-page-content")
        or soup.find("main")
        or soup.find("article")
        or soup.body
    )
    if content_el is None:
        return ""

    # script / style / nav / header / footer を除去
    for tag in content_el.find_all(["script", "style", "nav", "header", "footer"]):
        tag.decompose()

    text = content_el.get_text(separator="\n", strip=True)
    # 3000文字に切り詰め（Bedrockのコンテキスト節約）
    return text[:3000]
