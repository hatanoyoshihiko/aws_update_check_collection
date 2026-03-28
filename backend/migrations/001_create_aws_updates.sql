-- AWS Update Check Collection
-- Migration: 001_create_aws_updates
-- Aurora DSQL用スキーマ定義

CREATE TABLE IF NOT EXISTS aws_updates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    published_date  DATE NOT NULL,
    title           VARCHAR(500) NOT NULL,
    summary_en      TEXT,
    source_url      VARCHAR(1000) NOT NULL,
    page_summary_ja TEXT,
    use_cases_ja    TEXT,
    category        VARCHAR(200),
    collected_at    TIMESTAMP DEFAULT NOW(),
    created_at      TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_aws_updates_source_url UNIQUE (source_url)
);

CREATE INDEX ASYNC IF NOT EXISTS idx_aws_updates_published_date ON aws_updates(published_date);
CREATE INDEX ASYNC IF NOT EXISTS idx_aws_updates_category ON aws_updates(category);
