from dataclasses import dataclass

from app.db.models import Listing, SourceTrustLevel

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
    total_penalty = sum(signal.severity for signal in detect_scam_signals(listing))
    return max(0, 100 - total_penalty)
