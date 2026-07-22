"""The day and its parts — time is the real currency of this game.

A day is a budget of hours, not an infinite tape. People are out only at certain
parts of the day; the markets close; the dead keep the night. You spend the day
in visits and travel, then **sleep** to end it and wake to a new dawn. Managing
that budget — being in the right place at the right hour — matters more than money.

Pure functions over the smuggler's minute clock, so everything stays testable.
"""

from __future__ import annotations

DAY = 24 * 60
DAY_START = 6 * 60     # you wake at 06:00
LATE = 24 * 60         # past midnight, you're burning the night

# Ordered parts of the day. Each: (start_minute, key, glyph).
_PARTS = [
    (5 * 60, "morning", "\u2600"),    # 05:00–11:59  ☀
    (12 * 60, "afternoon", "\u26c5"),  # 12:00–16:59  ⛅
    (17 * 60, "evening", "\u263e"),    # 17:00–21:59  ☾ (dusk)
    (22 * 60, "night", "\u2735"),      # 22:00–04:59  ✵
]
PARTS = tuple(p[1] for p in _PARTS)


def part_of(minutes: int) -> str:
    m = minutes % DAY
    if 5 * 60 <= m < 12 * 60:
        return "morning"
    if 12 * 60 <= m < 17 * 60:
        return "afternoon"
    if 17 * 60 <= m < 22 * 60:
        return "evening"
    return "night"        # 22:00–04:59


def glyph(minutes: int) -> str:
    return dict((k, g) for _s, k, g in _PARTS)[part_of(minutes)]


def hhmm(minutes: int) -> str:
    m = minutes % DAY
    return f"{m // 60:02d}:{m % 60:02d}"


def label(minutes: int) -> str:
    """A short, readable time-of-day stamp: '☾ evening 18:30'."""
    return f"{glyph(minutes)} {part_of(minutes)} {hhmm(minutes)}"


def is_night(minutes: int) -> bool:
    return part_of(minutes) == "night"


def minutes_to_wake(minutes: int) -> int:
    """How many minutes of sleep until the next 06:00 dawn."""
    m = minutes % DAY
    return (DAY_START - m) if m < DAY_START else (DAY - m + DAY_START)
