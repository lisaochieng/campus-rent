from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import School

IGNORED_ACRONYM_WORDS = {"of", "the", "and", "at"}


def school_acronym(name: str) -> str:
    return "".join(
        word[0].upper()
        for word in name.replace(",", " ").split()
        if word.lower() not in IGNORED_ACRONYM_WORDS
    )


def find_school_by_name(db: Session, school_name: str) -> School | None:
    school = db.scalar(select(School).where(School.name.ilike(f"%{school_name}%")))
    if school is not None:
        return school

    normalized_query = school_name.strip().upper().replace(".", "")
    schools = db.scalars(select(School)).all()
    for candidate in schools:
        if school_acronym(candidate.name) == normalized_query:
            return candidate

    return None


def search_schools(db: Session, query: str, limit: int) -> list[School]:
    normalized_query = query.strip().upper().replace(".", "")
    schools = list(db.scalars(select(School).order_by(School.name)).all())
    matches = []

    for school in schools:
        acronym = school_acronym(school.name)
        searchable_text = f"{school.name} {school.city} {school.state}".lower()
        if query.lower() in searchable_text or acronym.startswith(normalized_query):
            matches.append(school)

    return matches[:limit]
