import json
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.housing_lead import HousingLeadRead
from app.services.external_school_search import find_or_fetch_school

router = APIRouter(prefix="/housing-leads", tags=["housing leads"])

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
EXCLUDED_TAG_VALUES = {
    "dormitory",
    "university",
    "college",
    "school",
    "student_accommodation",
}
EXCLUDED_TEXT_MARKERS = (
    "dormitory",
    "dorm",
    "residence hall",
    "student residence",
    "student housing",
    "college house",
)


def osm_query(latitude: Decimal, longitude: Decimal, radius_meters: int) -> str:
    lat = float(latitude)
    lon = float(longitude)
    return f"""
    [out:json][timeout:12];
    (
      node(around:{radius_meters},{lat},{lon})["building"="apartments"];
      way(around:{radius_meters},{lat},{lon})["building"="apartments"];
      relation(around:{radius_meters},{lat},{lon})["building"="apartments"];
      node(around:{radius_meters},{lat},{lon})["apartments"];
      way(around:{radius_meters},{lat},{lon})["apartments"];
    );
    out center tags 40;
    """


def address_from_tags(tags: dict) -> str | None:
    street = tags.get("addr:street")
    number = tags.get("addr:housenumber")
    city = tags.get("addr:city")
    if street and number:
        return ", ".join(part for part in [f"{number} {street}", city] if part)
    return tags.get("addr:full")


def lead_name(tags: dict, fallback: str) -> str:
    return (
        tags.get("name")
        or tags.get("operator")
        or tags.get("addr:housename")
        or fallback
    )


def element_coordinates(element: dict) -> tuple[Decimal | None, Decimal | None]:
    latitude = element.get("lat") or (element.get("center") or {}).get("lat")
    longitude = element.get("lon") or (element.get("center") or {}).get("lon")
    if latitude is None or longitude is None:
        return None, None
    return Decimal(str(latitude)), Decimal(str(longitude))


def overpass_source_url(element: dict) -> str:
    return f"https://www.openstreetmap.org/{element['type']}/{element['id']}"


def is_off_campus_apartment_lead(tags: dict) -> bool:
    normalized = {key: str(value).lower() for key, value in tags.items() if value is not None}
    for key in ("building", "amenity", "residential", "accommodation", "community"):
        if normalized.get(key) in EXCLUDED_TAG_VALUES:
            return False

    searchable_text = " ".join(
        normalized.get(key, "")
        for key in ("name", "operator", "description", "official_name", "alt_name")
    )
    if any(marker in searchable_text for marker in EXCLUDED_TEXT_MARKERS):
        return False

    return True


@router.get("/nearby", response_model=list[HousingLeadRead])
def get_nearby_housing_leads(
    school_name: str = Query(min_length=2),
    radius_meters: int = Query(default=2500, ge=500, le=8000),
    limit: int = Query(default=20, ge=1, le=40),
    db: Session = Depends(get_db),
) -> list[HousingLeadRead]:
    school = find_or_fetch_school(db, school_name)
    if school is None:
        return []

    request = Request(
        f"{OVERPASS_URL}?{urlencode({'data': osm_query(school.latitude, school.longitude, radius_meters)})}",
        headers={"User-Agent": "CampusRent student housing search (local development)"},
    )

    try:
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return []

    leads: list[HousingLeadRead] = []
    seen: set[str] = set()
    for element in payload.get("elements", []):
        latitude, longitude = element_coordinates(element)
        if latitude is None or longitude is None:
            continue

        tags = element.get("tags") or {}
        if not is_off_campus_apartment_lead(tags):
            continue

        lead_id = f"{element['type']}-{element['id']}"
        if lead_id in seen:
            continue
        seen.add(lead_id)

        leads.append(
            HousingLeadRead(
                id=lead_id,
                name=lead_name(tags, "Nearby apartment building"),
                address=address_from_tags(tags),
                latitude=latitude,
                longitude=longitude,
                source_url=overpass_source_url(element),
                website=tags.get("website") or tags.get("contact:website"),
                phone=tags.get("phone") or tags.get("contact:phone"),
                email=tags.get("email") or tags.get("contact:email"),
                source_name="OpenStreetMap Overpass",
            )
        )

    return leads[:limit]
