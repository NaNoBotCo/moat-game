"""The contribution layer: what the game collects, and why it is worth having.

Mot Dang holds 9,075 catalogued places in Chiang Mai. **7,109 of them have no
opening hours at all.** Hours are the single largest hole in the atlas, and they
are the hardest field to crawl, because they are not written down anywhere a
crawler can reach — they live in a hand-lettered card behind a grille, or in the
fact that the shutter is up when you walk past at nine.

Moat's core skill is reading windows. A player who has learned the lattice is a
person who habitually notices, at a specific minute, whether a specific place is
open. That is the exact observation the atlas is missing. This is the one place
where the game and the map want precisely the same thing from the same act, and
that is why the contribution layer is worth building at all — not because
gamified data collection is clever, but because the mechanic already *is* the
observation.

**Two hard rules, both inherited from Mot Dang's own worker.**

1. A player is a stranger. Mot Dang's claim endpoint deliberately accepts
   contact and presentational facts only, never a place's name, address, or
   coordinates, on the stated grounds that a stranger can get those wrong.
   The game respects that boundary exactly: an observation carries **a place
   id, a timestamp, and open-or-shut**, and nothing else. It never proposes a
   name, never moves a pin, never creates a place.

2. Nothing goes live. Contributions target the moderation queue — the path a
   human reads before anything is published — never a direct write. A game
   cannot be allowed to edit an atlas.

An observation is worth little on its own and a great deal in aggregate: twenty
players walking past the same shutter at twenty different minutes describe a
window that no single one of them could state.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# How many independent observations before a window is worth proposing at all.
MIN_OBSERVATIONS = 6
# ...and how many must agree before we'd call the edge of a window confident.
MIN_AGREEMENT = 0.75


@dataclass
class Observation:
    """One person, one place, one minute, open or shut. That is the whole thing."""
    place_id: str            # Mot Dang's own stable id, e.g. "cm-osm-node-1234"
    minute: int              # minutes past midnight, local
    weekday: int             # 0..6
    open: bool
    source: str = "play"     # "play" (in-game) | "field" (AR, real world)


@dataclass
class Window:
    """What a pile of observations adds up to."""
    place_id: str
    opens: int | None = None
    closes: int | None = None
    observations: int = 0
    agreement: float = 0.0
    confident: bool = False
    notes: list[str] = field(default_factory=list)


def log(pc, place_id: str, minute: int, weekday: int, is_open: bool,
        source: str = "play") -> None:
    """Record what the player just saw. Local only until exported."""
    obs = list(pc.observations)
    obs.append({"place_id": place_id, "minute": int(minute),
                "weekday": int(weekday), "open": bool(is_open),
                "source": source})
    pc.observations = obs[-4000:]


# The seam that matters. The game world's venues are fictionalised composites
# with invented hours — playing Moat teaches the skill of reading a window, but
# an in-game sighting describes nothing real and must never reach the atlas.
# Only observations made in the real city, of a real catalogued place, are
# exportable. `source` carries that distinction and `by_place` enforces it.
EXPORTABLE_SOURCES = ("field",)


def by_place(pc, sources: tuple[str, ...] = EXPORTABLE_SOURCES
             ) -> dict[str, list[dict]]:
    """Group observations by place. Defaults to real-world sightings only."""
    out: dict[str, list[dict]] = {}
    for o in pc.observations:
        if sources and o.get("source") not in sources:
            continue
        out.setdefault(o["place_id"], []).append(o)
    return out


def infer(records: list[dict]) -> Window:
    """Turn observations of one place into a proposed window, or admit we can't.

    Deliberately conservative. The opening edge is the earliest minute anybody
    ever saw it open; the closing edge the latest. Anything that contradicts
    lowers agreement, and low agreement means we propose nothing at all — a
    wrong hour in an atlas is worse than a missing one.
    """
    if not records:
        return Window("", observations=0)
    pid = records[0]["place_id"]
    opens = [r["minute"] for r in records if r["open"]]
    shuts = [r["minute"] for r in records if not r["open"]]
    w = Window(pid, observations=len(records))
    if not opens:
        w.notes.append("Never seen open. Not enough to say anything.")
        return w
    lo, hi = min(opens), max(opens)
    # Shut sightings *inside* the proposed span are the contradiction that matters.
    inside = [m for m in shuts if lo <= m <= hi]
    w.agreement = 1.0 - (len(inside) / max(1, len(records)))
    w.opens, w.closes = lo, hi
    w.confident = (w.observations >= MIN_OBSERVATIONS
                   and w.agreement >= MIN_AGREEMENT)
    if inside:
        w.notes.append(f"{len(inside)} sighting(s) shut inside the proposed "
                       f"span — the real window is probably split (a midday "
                       f"close), so this is offered as a range, not a rule.")
    if not w.confident:
        w.notes.append(f"Not proposing: {w.observations} observation(s), "
                       f"{w.agreement:.0%} agreement. Wants "
                       f"{MIN_OBSERVATIONS} and {MIN_AGREEMENT:.0%}.")
    return w


def ready(pc) -> list[Window]:
    """Every place we have enough to say something honest about."""
    return [w for w in (infer(rs) for rs in by_place(pc).values()) if w.confident]


def hhmm(m: int) -> str:
    return f"{m // 60:02d}:{m % 60:02d}"


def as_suggestion(w: Window) -> dict:
    """Shaped for the moderation queue — a note a human reads, not a write.

    Note what is absent: no name, no address, no coordinates, no claim of
    ownership, no contact details. Only the place id it refers to and what was
    observed about its hours.
    """
    return {
        "kind": "hours_observation",
        "placeId": w.place_id,
        "proposed": f"{hhmm(w.opens)}-{hhmm(w.closes)}",
        "observations": w.observations,
        "agreement": round(w.agreement, 2),
        "note": ("Aggregated from independent passer-by observations in the "
                 "game Moat. Each observation is one person recording whether "
                 "this place was open at one minute. No name, address or "
                 "location is proposed or implied. For a human to confirm "
                 "before anything is published."),
        "caveats": w.notes,
    }


def summary(pc) -> list[str]:
    places = by_place(pc)
    done = ready(pc)
    played = len(by_place(pc, sources=("play",)))
    lines = [f"Observations logged: {len(pc.observations):,} "
             f"across {len(places):,} real places"
             + (f" (plus {played} in-game, which stay in the game)."
                if played else ".")]
    if done:
        lines.append(f"{len(done):,} of them now have enough agreement to be "
                     f"worth offering to the atlas.")
    else:
        lines.append("None of them is settled enough to offer yet. Keep "
                     "walking past things.")
    return lines
