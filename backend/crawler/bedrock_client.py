"""Amazon Bedrock を使って記事の日本語要約・活用例を生成するモジュール"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass

import boto3

logger = logging.getLogger(__name__)

MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "jp.anthropic.claude-sonnet-4-6")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "ap-northeast-1")

_PROMPT_TEMPLATE = """\
以下のAWSアップデート記事の本文を読み、JSON形式のみで出力してください。
説明文や前置きは不要です。JSONだけを出力してください。

出力形式:
{{
  "title_ja": "記事タイトルの日本語訳（簡潔に）",
  "page_summary_ja": "日本語で300字以内の要約",
  "use_cases_ja": "- 活用例1\\n- 活用例2\\n- 活用例3"
}}

記事タイトル: {title}

記事本文:
{article_text}
"""


@dataclass
class BedrockResult:
    title_ja: str
    page_summary_ja: str
    use_cases_ja: str


def generate_summary(title: str, article_text: str) -> BedrockResult:
    """Bedrock で日本語要約・活用例を生成する"""
    client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)

    prompt = _PROMPT_TEMPLATE.format(title=title[:200], article_text=article_text)

    body = json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }
    )

    try:
        resp = client.invoke_model(
            modelId=MODEL_ID,
            body=body,
            contentType="application/json",
            accept="application/json",
        )
        raw = json.loads(resp["body"].read())
        text = raw["content"][0]["text"].strip()
        # JSON部分だけを抽出（前後に余分なテキストがある場合に対応）
        start = text.find("{")
        end = text.rfind("}") + 1
        parsed = json.loads(text[start:end])
        return BedrockResult(
            title_ja=parsed.get("title_ja", ""),
            page_summary_ja=parsed.get("page_summary_ja", ""),
            use_cases_ja=parsed.get("use_cases_ja", ""),
        )
    except Exception as e:
        logger.exception("Bedrock invocation failed: %s", e)
        raise
