import json
from uuid import UUID

from redis import Redis

from app.core.config import settings

FAST_SEARCH_CACHE_PREFIX = "fast-search"
FAST_SEARCH_CACHE_SECONDS = 60


def get_cache_client() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


def build_fast_search_cache_key(
    *,
    query: str,
    city: str | None,
    state: str | None,
    max_rent: int | None,
    min_scam_safety: int | None,
    limit: int,
) -> str:
    normalized = {
        "query": query.strip().lower(),
        "city": city.strip().lower() if city else None,
        "state": state.strip().lower() if state else None,
        "max_rent": max_rent,
        "min_scam_safety": min_scam_safety,
        "limit": limit,
    }
    return f"{FAST_SEARCH_CACHE_PREFIX}:{json.dumps(normalized, sort_keys=True)}"


def get_cached_listing_ids(cache_key: str) -> list[UUID] | None:
    cached_value = get_cache_client().get(cache_key)
    if cached_value is None:
        return None

    return [UUID(value) for value in json.loads(cached_value)]


def set_cached_listing_ids(cache_key: str, listing_ids: list[UUID]) -> None:
    serialized = json.dumps([str(listing_id) for listing_id in listing_ids])
    get_cache_client().setex(cache_key, FAST_SEARCH_CACHE_SECONDS, serialized)


def clear_fast_search_cache() -> int:
    client = get_cache_client()
    keys = list(client.scan_iter(f"{FAST_SEARCH_CACHE_PREFIX}:*"))
    if not keys:
        return 0

    return int(client.delete(*keys))
