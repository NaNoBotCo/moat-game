"""The coucal clock — the one authoritative time in this world.

Somebody set it in a wat fifty years ago and it has not stopped since. Nobody
alive remembers who, and nobody has thought to correct it, because everything
that matters in this city was long ago set *by* it: shop windows, tout shifts,
monk rounds, checkpoint rotations, the hour a fence will open a back door.

It does not agree with your watch. It keeps eight **watches** to the day, and
its day begins thirty-seven minutes after civil midnight — a drift nobody
bothered to fix, because the city keeps time by the bird and not by the phone.

That is the whole trick of the opening. Your clock says 11:00 and the shop is
shut; it opens at 11:37 and closes at 14:37, and the clinic down the lane opens
at 17:37, and the tout on the corner changes shift at 08:37, and none of that
looks like a pattern **until you stop measuring it against your own clock**.
Against each other the windows are perfectly regular. They always were.

No entity in the game keeps private time. Everything asks this module.

    watch_of(minutes)      which of the eight watches a civil minute falls in
    residue(minutes)       how far past a watch boundary you are — the tell
    on_boundary(minutes)   are you standing at the hinge of a watch
    call_hours()           the watches at which the bird is heard
"""

from __future__ import annotations

# The drift. Set once, fifty years ago, by a hand nobody can name.
OFFSET = 37                       # minutes past civil midnight that watch 0 opens
WATCHES = 8                       # watches to a day
WATCH_MINUTES = (24 * 60) // WATCHES     # 180 — three hours each
DAY = 24 * 60

# What each watch is for, in the city's own reckoning. These are the names the
# lattice is described by once the player can finally see it.
WATCH_NAMES = (
    "the still watch",        # 00:37 – 03:37
    "the cold watch",         # 03:37 – 06:37
    "the opening watch",      # 06:37 – 09:37
    "the trading watch",      # 09:37 – 12:37
    "the low watch",          # 12:37 – 15:37
    "the turning watch",      # 15:37 – 18:37
    "the lit watch",          # 18:37 – 21:37
    "the quiet watch",        # 21:37 – 00:37
)

# The bird is heard at the hinge of these watches, and only these.
CALL_WATCHES = (2, 5, 7)

# How close to a hinge still counts as standing on it.
BOUNDARY_SLACK = 6


def watch_of(minutes: int) -> int:
    """Which watch a civil minute falls into, 0..7."""
    return ((minutes - OFFSET) % DAY) // WATCH_MINUTES


def watch_name(minutes: int) -> str:
    return WATCH_NAMES[watch_of(minutes)]


def watch_start(index: int) -> int:
    """The civil minute a watch opens."""
    return (OFFSET + index * WATCH_MINUTES) % DAY


def residue(minutes: int) -> int:
    """Minutes past the opening of the current watch. Zero at the hinge."""
    return ((minutes - OFFSET) % DAY) % WATCH_MINUTES


def to_next_boundary(minutes: int) -> int:
    r = residue(minutes)
    return WATCH_MINUTES - r if r else 0


def on_boundary(minutes: int, slack: int = BOUNDARY_SLACK) -> bool:
    """Are you standing at the hinge of a watch — either side of it."""
    r = residue(minutes)
    return r <= slack or r >= (WATCH_MINUTES - slack)


def crossings(start: int, end: int) -> list[int]:
    """Every watch hinge strictly between two civil minutes (absolute times)."""
    out = []
    first = start + to_next_boundary(start) if residue(start) else start
    m = first
    while m <= end:
        out.append(m)
        m += WATCH_MINUTES
    return out


def is_call(minutes: int, slack: int = BOUNDARY_SLACK) -> bool:
    """Is the bird sounding right now?"""
    return on_boundary(minutes, slack) and _nearest_watch(minutes) in CALL_WATCHES


def _nearest_watch(minutes: int) -> int:
    r = residue(minutes)
    w = watch_of(minutes)
    return (w + 1) % WATCHES if r >= (WATCH_MINUTES - BOUNDARY_SLACK) else w


def next_call(minutes: int) -> int:
    """Minutes from now until the bird next sounds."""
    for step in range(0, DAY + 1):
        if is_call((minutes + step) % DAY, slack=0):
            return step
    return 0


def hhmm(minutes: int) -> str:
    m = minutes % DAY
    return f"{m // 60:02d}:{m % 60:02d}"


def label(minutes: int) -> str:
    """How the lattice reads, once you can see it at all."""
    w = watch_of(minutes)
    return (f"{WATCH_NAMES[w]} ({hhmm(watch_start(w))}"
            f"–{hhmm(watch_start((w + 1) % WATCHES))}), "
            f"{residue(minutes)} in")


# --- keying the city to the bird -------------------------------------------
def true_window(seed_key: str) -> tuple[int, int]:
    """The window a thing *actually* keeps, keyed to the bird rather than to a
    shop sign. Deterministic from the entity's key, so it is save-stable and
    identical for every player: the city did not roll dice for this either."""
    h = 0
    for ch in seed_key:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    start_watch = h % WATCHES
    length = WATCH_MINUTES if (h >> 8) % 3 else WATCH_MINUTES // 3
    o = watch_start(start_watch)
    return o, (o + length) % DAY


def span(seed_key: str, watches: int = 3) -> tuple[int, int]:
    """A window several watches wide, keyed to the bird. Used for the places
    that keep long hours — a market floor is open most of a working day, but
    it still opens and shuts on the watch and not on your wristwatch."""
    h = 0
    for ch in seed_key:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    o = watch_start(h % WATCHES)
    return o, (o + watches * WATCH_MINUTES) % DAY


def open_at(window: tuple[int, int], minutes: int) -> bool:
    o, c = window
    m = minutes % DAY
    return (o <= m < c) if o < c else (m >= o or m < c)
