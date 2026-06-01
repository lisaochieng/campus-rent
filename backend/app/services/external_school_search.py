import json
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import School
from app.schemas.school import SchoolCreate
from app.services.school_matching import find_school_by_name

OPENALEX_INSTITUTIONS_URL = "https://api.openalex.org/institutions"


def normalize_region(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) <= 3:
        return cleaned.upper()
    return cleaned.title()


def search_openalex_schools(query: str, limit: int) -> list[SchoolCreate]:
    params = urlencode(
        {
            "search": query,
            "filter": "type:education",
            "per-page": min(limit, 25),
        }
    )
    request = Request(
        f"{OPENALEX_INSTITUTIONS_URL}?{params}",
        headers={
            "Accept": "application/json",
            "User-Agent": "CampusRent student housing search (local development)",
        },
    )

    try:
        with urlopen(request, timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return []

    schools: list[SchoolCreate] = []
    for institution in payload.get("results", []):
        geo = institution.get("geo") or {}
        latitude = geo.get("latitude")
        longitude = geo.get("longitude")
        city = geo.get("city")
        country_code = geo.get("country_code")
        if latitude is None or longitude is None or not city or not country_code:
            continue

        schools.append(
            SchoolCreate(
                name=institution["display_name"],
                city=city,
                state=geo.get("region") or city,
                country=country_code,
                latitude=Decimal(str(latitude)),
                longitude=Decimal(str(longitude)),
            )
        )

    return schools


def upsert_external_school(db: Session, payload: SchoolCreate) -> School:
    existing = db.scalar(select(School).where(School.name.ilike(payload.name)))
    if existing is not None:
        return existing

    school = School(
        name=payload.name.strip(),
        city=payload.city.strip().title(),
        state=normalize_region(payload.state),
        country=payload.country.strip().upper(),
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    db.add(school)
    db.flush()
    return school


def find_or_fetch_school(db: Session, school_name: str) -> School | None:
    existing = find_school_by_name(db, school_name)
    if existing is not None:
        return existing

    matches = search_openalex_schools(school_name, limit=1)
    if not matches:
        return None

    school = upsert_external_school(db, matches[0])
    db.commit()
    db.refresh(school)
    return school
