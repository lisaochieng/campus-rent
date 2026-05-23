from secrets import compare_digest

from fastapi import Header, HTTPException, status
from opensearchpy import OpenSearch
import psycopg
from redis import Redis

from app.core.config import settings


def require_ingestion_api_key(
    x_ingestion_api_key: str | None = Header(default=None),
) -> None:
    if x_ingestion_api_key is None or not compare_digest(
        x_ingestion_api_key,
        settings.ingestion_api_key,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid ingestion API key required.",
        )


def check_postgres() -> bool:
    try:
        with psycopg.connect(settings.postgres_driver_dsn, connect_timeout=2) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return cursor.fetchone() == (1,)
    except Exception:
        return False


def check_redis() -> bool:
    try:
        client = Redis.from_url(settings.redis_url, socket_connect_timeout=2)
        return bool(client.ping())
    except Exception:
        return False


def check_opensearch() -> bool:
    try:
        client = OpenSearch(settings.opensearch_url, timeout=2)
        return bool(client.ping())
    except Exception:
        return False
