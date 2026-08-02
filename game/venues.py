"""The venue layer: the city's shopfronts, and who is allowed to be named.

Two layers sit in one file (`data/venues.json`, built by
`tools/import_motdang.py` from the Mot Dang catalogue):

**The anchor layer** — real, named, permissioned businesses. A player learns the
city by them. They may only ever be depicted doing their actual trade: you buy
from them, eat at them, learn from them, meet people at them. They are never
fronts, never fences, never drops, never raided.

**The shadow layer** — fictional composites, identity stripped at import. All
the criminal economy lives here. These carry the fronts, the drops, the touts,
and the narrow windows the smuggler learns to read.

**Consent is a dead-man's switch.** A grant carries an expiry. Past it the
permission lapses on its own and the venue silently falls back to its fictional
composite — no code change, no content rewrite, no rebuild. Silence un-names a
business rather than naming it forever, which is the failure direction we want.
Nothing in the game reads `consent["status"]` directly; everything asks
`live_consent()`, which is closed by default and refuses anything malformed.
"""

from __future__ import annotations

import datetime as _dt
import json
import pathlib
from dataclasses import dataclass

DATA = pathlib.Path(__file__).resolve().parent.parent / "data" / "venues.json"

# How long before a lapsing grant we should be back on the doorstep asking.
RENEWAL_WARNING_DAYS = 30


def _parse(day: str | None) -> _dt.date | None:
    try:
        return _dt.date.fromisoformat(day) if day else None
    except (ValueError, TypeError):
        return None


def live_consent(consent: dict, today: _dt.date | None = None) -> bool:
    """True only for a grant that is present, well-formed, and unexpired.

    Closed by default: anything missing, malformed, withdrawn or past its
    expiry reads as no permission at all.
    """
    if not isinstance(consent, dict):
        return False
    if consent.get("status") != "granted":
        return False
    if not consent.get("real_name"):
        return False
    expires = _parse(consent.get("expires_on"))
    if expires is None:          # a grant with no end date is not a grant
        return False
    return (today or _dt.date.today()) <= expires


def days_left(consent: dict, today: _dt.date | None = None) -> int | None:
    expires = _parse(consent.get("expires_on"))
    if expires is None:
        return None
    return (expires - (today or _dt.date.today())).days


@dataclass(frozen=True)
class Venue:
    key: str
    district: str
    cat: str
    sub: str
    descriptor: str
    open: int | None
    close: int | None
    narrow: bool
    consent: dict

    def name(self, today: _dt.date | None = None) -> str:
        """What the player is shown. A real name only while consent is live."""
        if live_consent(self.consent, today):
            return self.consent["real_name"]
        return self.descriptor

    def is_anchor(self, today: _dt.date | None = None) -> bool:
        """Anchors are real businesses. They never take a criminal role."""
        return live_consent(self.consent, today)

    def can_be_front(self, today: _dt.date | None = None) -> bool:
        """Only fictional composites may carry the shadow layer.

        Once a venue has *ever* been named under consent it is barred from the
        shadow layer for good, even after the grant lapses. A player who learned
        a real name in that slot would join the dots when the same slot later
        turned out to be a drop, and a lapsed permission is exactly when we can
        least afford that.
        """
        if self.consent.get("real_name"):
            return False
        return not self.is_anchor(today)

    def open_at(self, minutes: int) -> bool:
        if self.open is None or self.close is None:
            return True                  # unknown hours: assume it's a shopfront
        m = minutes % (24 * 60)
        if self.close <= 24 * 60:
            return self.open <= m < self.close
        return m >= self.open or m < (self.close - 24 * 60)   # closes past midnight

    def window_label(self) -> str:
        if self.open is None or self.close is None:
            return "hours unknown"
        if self.open == 0 and self.close >= 24 * 60:
            return "all hours"
        def hhmm(x: int) -> str:
            x %= 24 * 60
            return f"{x // 60:02d}:{x % 60:02d}"
        return f"{hhmm(self.open)}–{hhmm(self.close)}"


_CACHE: dict | None = None


def _load() -> dict:
    global _CACHE
    if _CACHE is None:
        if not DATA.exists():
            _CACHE = {"venues": [], "count": 0, "density": {}, "attribution": ""}
        else:
            _CACHE = json.loads(DATA.read_text())
    return _CACHE


def all_venues() -> list[Venue]:
    return [Venue(v["key"], v["district"], v["cat"], v["sub"], v["descriptor"],
                  v.get("open"), v.get("close"), v.get("narrow", False),
                  v.get("consent", {}))
            for v in _load().get("venues", [])]


def in_district(district: str) -> list[Venue]:
    return [v for v in all_venues() if v.district == district]


def open_now(district: str, minutes: int) -> list[Venue]:
    return [v for v in in_district(district) if v.open_at(minutes)]


def narrow_windows(district: str) -> list[Venue]:
    """The shopfronts whose true function is a schedule, not a trade."""
    return [v for v in in_district(district) if v.narrow and v.can_be_front()]


def anchors(district: str, today: _dt.date | None = None) -> list[Venue]:
    return [v for v in in_district(district) if v.is_anchor(today)]


def attribution() -> str:
    return _load().get("attribution", "")


def consent_report(today: _dt.date | None = None) -> dict:
    """Operational view: who is live, who lapses soon, who has gone stale."""
    today = today or _dt.date.today()
    live, expiring, lapsed, pending = [], [], [], []
    for v in all_venues():
        c = v.consent
        status = c.get("status")
        if status == "pending":
            pending.append(v)
        elif status == "granted":
            if live_consent(c, today):
                live.append(v)
                d = days_left(c, today)
                if d is not None and d <= RENEWAL_WARNING_DAYS:
                    expiring.append((d, v))
            else:
                lapsed.append(v)
    expiring.sort(key=lambda dv: dv[0])
    return {"live": live, "expiring": expiring, "lapsed": lapsed,
            "pending": pending}
