from opensearchpy import OpenSearch
import psycopg
from redis import Redis

from app.core.config import settings


def check_postgres() -> bool:
    try:
        with psycopg.connect(settings.postgres_dsn, connect_timeout=2) as connection:
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
