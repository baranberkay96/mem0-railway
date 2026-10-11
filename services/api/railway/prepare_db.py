"""Pre-deploy step 1: wait for Postgres, then create Mem0's app database.

Upstream's docker-compose creates the app database (APP_DB_NAME, default
mem0_app) with an init script mounted into the Postgres container. Railway
cannot mount files into an image service, so this does the same from the API
image: it waits for Postgres (services start in parallel on Railway), enables
pgvector in the vector database and creates the app database if it is missing.
Alembic migrations run right after this script (see preDeployCommand).
"""

from __future__ import annotations

import os
import sys
import time

import psycopg
from psycopg import sql


def _settings() -> dict[str, str]:
    return {
        "host": os.environ.get("POSTGRES_HOST", "postgres"),
        "port": os.environ.get("POSTGRES_PORT", "5432"),
        "user": os.environ.get("POSTGRES_USER", "postgres"),
        "password": os.environ.get("POSTGRES_PASSWORD", ""),
        "vector_db": os.environ.get("POSTGRES_DB", "postgres"),
        "app_db": os.environ.get("APP_DB_NAME", "mem0_app"),
    }


def _connect(cfg: dict[str, str], dbname: str) -> psycopg.Connection:
    return psycopg.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        dbname=dbname,
        connect_timeout=5,
        autocommit=True,
    )


def wait_for_postgres(cfg: dict[str, str], timeout_s: int) -> psycopg.Connection:
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            return _connect(cfg, cfg["vector_db"])
        except psycopg.OperationalError as exc:
            if time.monotonic() > deadline:
                sys.exit(f"prepare_db: Postgres at {cfg['host']}:{cfg['port']} not ready after {timeout_s}s: {exc}")
            print(f"prepare_db: waiting for Postgres ({exc.__class__.__name__})", flush=True)
            time.sleep(3)


def main() -> None:
    cfg = _settings()
    if not cfg["password"]:
        sys.exit("prepare_db: POSTGRES_PASSWORD is empty")
    timeout_s = int(os.environ.get("DB_WAIT_SECONDS", "300"))

    with wait_for_postgres(cfg, timeout_s) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        exists = conn.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (cfg["app_db"],)
        ).fetchone()
        if exists:
            print(f"prepare_db: database {cfg['app_db']} already exists", flush=True)
        else:
            conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(cfg["app_db"])))
            print(f"prepare_db: created database {cfg['app_db']}", flush=True)


if __name__ == "__main__":
    main()
