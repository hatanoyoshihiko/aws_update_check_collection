"""Aurora DSQL connection utilities - shared Lambda Layer module"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

import boto3
import psycopg

DSQL_ENDPOINT = os.environ["DSQL_ENDPOINT"]
DSQL_REGION = os.environ.get("AWS_REGION", os.environ.get("DSQL_REGION", "ap-northeast-1"))
DB_NAME = os.environ.get("DSQL_DATABASE", "postgres")


def get_auth_token() -> str:
    client = boto3.client("dsql", region_name=DSQL_REGION)
    return client.generate_db_connect_admin_auth_token(
        Hostname=DSQL_ENDPOINT,
        Region=DSQL_REGION,
    )


@contextmanager
def get_connection(autocommit: bool = False) -> Generator[psycopg.Connection, None, None]:
    token = get_auth_token()
    conn = psycopg.connect(
        host=DSQL_ENDPOINT,
        dbname=DB_NAME,
        user="admin",
        password=token,
        sslmode="require",
        autocommit=autocommit,
    )
    try:
        yield conn
    finally:
        conn.close()
