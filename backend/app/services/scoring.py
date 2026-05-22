from decimal import Decimal
from math import asin, cos, radians, sin, sqrt

from app.db.models import Listing, School

EARTH_RADIUS_MILES = 3958.8


def calculate_distance_miles(
    start_latitude: Decimal,
    start_longitude: Decimal,
    end_latitude: Decimal,
    end_longitude: Decimal,
) -> float:
    start_lat = radians(float(start_latitude))
    start_lon = radians(float(start_longitude))
    end_lat = radians(float(end_latitude))
    end_lon = radians(float(end_longitude))

    lat_delta = end_lat - start_lat
    lon_delta = end_lon - start_lon

    haversine_value = (
        sin(lat_delta / 2) ** 2
        + cos(start_lat) * cos(end_lat) * sin(lon_delta / 2) ** 2
    )
    return 2 * EARTH_RADIUS_MILES * asin(sqrt(haversine_value))


def distance_score(distance_miles: float) -> int:
    if distance_miles <= 0.5:
        return 100
    if distance_miles <= 1:
        return 90
    if distance_miles <= 2:
        return 75
    if distance_miles <= 5:
        return 55
    if distance_miles <= 10:
        return 30

    return 10


def affordability_score(monthly_rent: int, max_budget: int | None) -> int:
    if max_budget is None:
        return 75

    if monthly_rent <= max_budget * 0.8:
        return 100
    if monthly_rent <= max_budget:
        return 85
    if monthly_rent <= max_budget * 1.15:
        return 50

    return 15


def campus_rent_score(
    *,
    listing: Listing,
    school: School,
    max_budget: int | None,
) -> dict[str, float | int]:
    if listing.latitude is None or listing.longitude is None:
        distance = 999.0
    else:
        distance = calculate_distance_miles(
            school.latitude,
            school.longitude,
            listing.latitude,
            listing.longitude,
        )

    distance_component = distance_score(distance)
    affordability_component = affordability_score(listing.monthly_rent, max_budget)
    freshness_component = 80
    scam_risk_component = 100

    total = round(
        (distance_component * 0.35)
        + (affordability_component * 0.35)
        + (freshness_component * 0.15)
        + (scam_risk_component * 0.15)
    )

    return {
        "distance_miles": round(distance, 2),
        "distance_score": distance_component,
        "affordability_score": affordability_component,
        "freshness_score": freshness_component,
        "scam_safety_score": scam_risk_component,
        "campus_rent_score": total,
    }
