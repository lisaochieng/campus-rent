from dataclasses import dataclass

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db.models import Listing, ScamSignal, SourceTrustLevel

SUSPICIOUS_PHRASES = (
    "wire money",
    "western union",
    "moneygram",
    "urgent",
    "act fast",
    "out of country",
    "no tour",
    "no viewing",
    "cash only",
    "deposit before viewing",
)


@dataclass(frozen=True)
class ScamSignalResult:
    signal_type: str
    severity: int
    explanation: str


def detect_scam_signals(listing: Listing) -> list[ScamSignalResult]:
    signals: list[ScamSignalResult] = []
    text = f"{listing.title} {listing.description or ''}".lower()

    for phrase in SUSPICIOUS_PHRASES:
        if phrase in text:
            signals.append(
                ScamSignalResult(
                    signal_type="suspicious_language",
                    severity=30,
                    explanation=f"Listing text contains suspicious phrase: '{phrase}'.",
                )
            )

    if not listing.address:
        signals.append(
            ScamSignalResult(
                signal_type="missing_address",
                severity=20,
                explanation="Listing does not include a street address.",
            )
        )

    if listing.latitude is None or listing.longitude is None:
        signals.append(
            ScamSignalResult(
                signal_type="missing_coordinates",
                severity=15,
                explanation="Listing is missing coordinates, so distance cannot be verified.",
            )
        )

    if listing.monthly_rent < 900:
        signals.append(
            ScamSignalResult(
                signal_type="unusually_low_rent",
                severity=25,
                explanation="Listing rent is unusually low for major campus rental markets.",
            )
        )

    if listing.source.trust_level in {SourceTrustLevel.LOW, SourceTrustLevel.UNKNOWN}:
        signals.append(
            ScamSignalResult(
                signal_type="weak_source_trust",
                severity=20,
                explanation="Listing comes from a source with weak or unknown trust level.",
            )
        )

    return signals


def scam_safety_score(listing: Listing) -> int:
    if listing.scam_signals:
        total_penalty = sum(signal.severity for signal in listing.scam_signals)
    else:
        total_penalty = sum(signal.severity for signal in detect_scam_signals(listing))

    return max(0, 100 - total_penalty)


def refresh_persisted_scam_signals(db: Session, listing: Listing) -> list[ScamSignal]:
    detected_signals = detect_scam_signals(listing)

    db.execute(delete(ScamSignal).where(ScamSignal.listing_id == listing.id))
    persisted_signals = [
        ScamSignal(
            listing_id=listing.id,
            signal_type=signal.signal_type,
            severity=signal.severity,
            explanation=signal.explanation,
            evidence={"source_url": listing.source_url},
        )
        for signal in detected_signals
    ]
    db.add_all(persisted_signals)
    db.flush()

    return persisted_signals
